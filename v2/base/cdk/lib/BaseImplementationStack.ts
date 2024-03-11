// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as seedrandom from "seedrandom"
import { Construct } from "constructs"
import * as cdk from "aws-cdk-lib"
import { aws_iam as iam } from "aws-cdk-lib"
import * as s3 from "aws-cdk-lib/aws-s3"
import { IotThingCertPolicy } from "@cdkConstructs/IotThingCertPolicy"
import { IotRoleAlias } from "@cdkConstructs/IotRoleAlias"
import { IotThingGroup } from "@cdkConstructs/IotThingGroup"
import { GreengrassV2Component } from "@cdkConstructs/GreengrassV2Component"
import { GreengrassV2Deployment } from "@cdkConstructs/GreengrassV2Deployment"
import * as myConst from "./Constants"

export class BaseImplementationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const stackName = cdk.Stack.of(this).stackName
    if (stackName.length > 20) {
      console.error("Stack name must be less than 20 characters in length")
      process.exitCode = 1
    }
    // suffix to use for all stack resources to make unique
    // In this stack all resources will use the format STACKNAME-RESOURCENAME-RANDOMSUFFIX

    const stackRandom: string = makeid(8, stackName)
    // Layered constructs - each constructs derived values can be used for subsequent constructs

    // create S3 bucket for artifacts - greengrass-component-artifacts-stackRandom-AccountId-Region
    // NOTE: This bucket and all contents will be deleted upon stack deletion
    const componentBucketName = `${cdk.Stack.of(this).stackName}-ggcomponents-${cdk.Fn.ref("AWS::AccountId")}-${cdk.Fn.ref("AWS::Region")}`
    const componentBucket = new s3.Bucket(this, "ComponentBucket", {
      bucketName: componentBucketName,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: s3.BucketEncryption.S3_MANAGED,
      autoDeleteObjects: true
    })

    // Create IoT role alias for use by Greengrass core
    const greengrassRoleMinimalPolicy = new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            "iot:DescribeCertificate",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogStreams",
            "iot:Connect",
            "iot:Publish",
            "iot:Subscribe",
            "iot:Receive",
            "s3:GetBucketLocation"
          ],
          resources: ["*"]
        }),
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["s3:GetObject"],
          resources: [`arn:aws:s3:::${componentBucketName}/*`]
        })
      ]
    })

    // Define stack-specific names for IoT role alias
    const roleAliasName = fullResourceName({
      stackName: stackName,
      baseName: "GreengrassV2TokenExchangeRole",
      suffix: stackRandom,
      resourceRegex: "\\w=,@-",
      maxLength: 128
    })
    const iamRoleName = fullResourceName({
      stackName: stackName,
      baseName: "RoleForIoTRoleAlias",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 64
    })
    // Then create IoT role alias
    const greengrassRoleAlias = new IotRoleAlias(this, "IoTRoleAlias", {
      iotRoleAliasName: roleAliasName,
      iamRoleName: iamRoleName,
      iamPolicy: greengrassRoleMinimalPolicy
    })

    // Define stack-specific names for the IoT thing name and policy
    const greengrassCoreThingName = fullResourceName({
      stackName: stackName,
      baseName: "greengrass-core",
      suffix: stackRandom,
      resourceRegex: "a-zA-Z0-9:_-",
      maxLength: 128
    })
    const greengrassCoreIotPolicyName = fullResourceName({
      stackName: stackName,
      baseName: "greengrass-minimal-policy",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 128
    })
    // Then create IoT thing, certificate/private key, and IoT Policy
    const iotThingCertPol = new IotThingCertPolicy(this, "GreengrassCore", {
      thingName: greengrassCoreThingName,
      iotPolicyName: greengrassCoreIotPolicyName,
      iotPolicy: myConst.greengrassCoreMinimalIoTPolicy,
      encryptionAlgorithm: "RSA",
      policyParameterMapping: {
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId"),
        rolealiasname: greengrassRoleAlias.roleAliasName
      }
    })

    // Define stack-specific name of the IoT thing group
    const groupName = fullResourceName({
      stackName: stackName,
      baseName: "greengrass-deployment-group",
      suffix: stackRandom,
      resourceRegex: "a-zA-Z0-9:_-",
      maxLength: 128
    })
    // Then create thing group and add thing
    const deploymentGroup = new IotThingGroup(this, "DeploymentGroup", {
      thingGroupName: groupName
    })
    deploymentGroup.addThing(iotThingCertPol.thingArn)

    // Greengrass component process

    // Create Hello World component
    // uses same component file name and path as AWS published components,
    // see the source recipe file for more details
    const componentName = "ggAccel.example.HelloWorld"
    const componentVersion = "1.0.0"
    const helloWorldComponent = new GreengrassV2Component(this, "HelloWorldComponent", {
      componentName: componentName,
      componentVersion: componentVersion,
      bucket: componentBucket,
      artifactZipPrefix: `${componentName}/${componentVersion}/`,
      targetArtifactKeyName: `${componentName}.zip`,
      sourceArtifactPath: path.join(__dirname, "..", "components", componentName, "artifacts", componentName, componentVersion),
      sourceRecipeFile: path.join(__dirname, "..", "components", componentName, `${componentName}-${componentVersion}.yaml`)
    })

    // Create the deployment with AWS public and stack components, target the thing group
    // and add the components/version/updates
    const greengrassDeployment = new GreengrassV2Deployment(this, "GreengrassDeployment", {
      targetArn: deploymentGroup.thingGroupArn,
      deploymentName: `${this.stackName} - Example deployment`,
      component: {
        // accelerator component(s)
        [helloWorldComponent.componentName]: {
          componentVersion: helloWorldComponent.componentVersion,
          configurationUpdate: {
            merge: JSON.stringify({
              Message: "Welcome from the Greengrass accelerator stack"
            })
          }
        }
      }
      // Optionally deployment policies can be added to the deployment
      // deploymentPolicies: {
      //   failureHandlingPolicy: "DO_NOTHING"
      // }
    })
    // Add core public components
    greengrassDeployment.addComponent({
      "aws.greengrass.Nucleus": {
        componentVersion: "2.10.3"
      },
      "aws.greengrass.Cli": {
        componentVersion: "2.10.3"
      }
    })
    greengrassDeployment.addComponent({
      "aws.greengrass.LocalDebugConsole": {
        componentVersion: "2.3.0",
        configurationUpdate: {
          merge: JSON.stringify({
            httpsEnabled: "false"
          })
        }
      }
    })

    // Set stack outputs to be consumed by local processes
    new cdk.CfnOutput(this, "ComponentBucketArn", {
      exportName: `${stackName}-ComponentBucketArn`,
      value: componentBucket.bucketArn
    })
    new cdk.CfnOutput(this, "IotRoleAliasName", {
      value: greengrassRoleAlias.roleAliasName
    })
    new cdk.CfnOutput(this, "ThingArn", {
      exportName: `${stackName}-ThingArn`,
      value: iotThingCertPol.thingArn
    })
    new cdk.CfnOutput(this, "ThingName", {
      exportName: `${stackName}-ThingName`,
      value: greengrassCoreThingName
    })
    new cdk.CfnOutput(this, "IotPolicyArn", {
      value: iotThingCertPol.iotPolicyArn
    })
    new cdk.CfnOutput(this, "RoleAliasArn", {
      value: greengrassRoleAlias.roleAliasArn
    })
    new cdk.CfnOutput(this, "IamRoleArn", {
      exportName: `${stackName}-IamRoleArn`,
      value: greengrassRoleAlias.iamRoleArn
    })
    new cdk.CfnOutput(this, "CertificateArn", {
      exportName: `${stackName}-CertificateArn`,
      value: iotThingCertPol.certificateArn
    })
    new cdk.CfnOutput(this, "CertificatePemParameter", {
      value: iotThingCertPol.certificatePemParameter
    })
    new cdk.CfnOutput(this, "PrivateKeySecretParameter", {
      value: iotThingCertPol.privateKeySecretParameter
    })
    new cdk.CfnOutput(this, "DataAtsEndpointAddress", {
      value: iotThingCertPol.dataAtsEndpointAddress
    })
    new cdk.CfnOutput(this, "CredentialProviderEndpointAddress", {
      value: iotThingCertPol.credentialProviderEndpointAddress
    })

    // ************ End of CDK Constructs / stack - Supporting functions below ************

    function makeid(length: number, seed: string) {
      // Generate a n-length random value for each resource
      var result = ""
      var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
      var charactersLength = characters.length
      seedrandom(seed, { global: true })
      for (var i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength))
      }
      return result
    }

    interface ResourceName {
      stackName: string
      baseName: string
      suffix: string
      resourceRegex: string
      maxLength: number
    }

    function fullResourceName({ stackName, baseName, suffix, resourceRegex, maxLength }: ResourceName) {
      let re = new RegExp(`[^\\[${resourceRegex}]`, "g")
      let resourceName = `${stackName}-${baseName}`.replace(re, "")
      resourceName = resourceName.substring(0, maxLength - suffix.length - 1)
      resourceName = `${resourceName}-${suffix}`
      return resourceName
    }
  }
}
