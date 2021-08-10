// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as iam from "@aws-cdk/aws-iam"
import * as s3 from "@aws-cdk/aws-s3"
import { IotPolicy } from "./IotPolicy/IotPolicy"
import { IotThingGroup } from "../../../base/cdk/lib/IotThingGroup/IotThingGroup"
import { GreengrassV2Component } from "../../../base/cdk/lib/GreengrassV2Component/GreengrassV2Component"
import { GreengrassV2Deployment } from "../../../base/cdk/lib/GreengrassV2Deployment/GreengrassV2Deployment"

import * as myConst from "./Constants"

export class OsCommandStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    if (cdk.Stack.of(this).stackName.length > 20) {
      console.error("Stack name must be less than 20 characters in length")
      process.exitCode = 1
    }
    const parentStack = this.node.tryGetContext("baseStack")
    if (parentStack === undefined) {
      console.error('Parent stack must be provided with --context baseStack="gg-accel-base" argument for "cdk deploy" or "cdk destroy"')
      process.exitCode = 1
    }

    // suffix to use for all stack resources to make unique
    // In this stack all resources will use the format STACKNAME-RESOURCENAME-RANDOMSUFFIX
    const stackRandom: string = makeid(8)

    // Load parameters from parent stack
    const thingArn = cdk.Fn.importValue(`${parentStack}-ThingArn`)
    const certificateArn = cdk.Fn.importValue(`${parentStack}-CertificateArn`)
    const iamRoleArn = cdk.Fn.importValue(`${parentStack}-IamRoleArn`)
    const componentBucketArn = cdk.Fn.importValue(`${parentStack}-ComponentBucketArn`)

    // Local variables
    const thingName = thingArn.split("/").slice(-1)[0]

    // Layered constructs - each constructs derived values can be used for subsequent constructs

    // Create IoT policy and attach to certificate
    const osCommandPolicyName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "gg-accel-os-command",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 128
    })
    const iotPolicy = new IotPolicy(this, "OsCommandIotPolicy", {
      iotPolicyName: osCommandPolicyName,
      iotPolicy: myConst.osCommandIoTPolicy,
      certificateArn: certificateArn,
      policyParameterMapping: {
        thingname: thingName,
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId")
      }
    })
    // Add an inline policy to the IAM role used by the IoT role alias
    const osCommandInlinePolicy = new iam.Policy(this, "OsCommandPolicy", {
      policyName: "OsCommandAccelerator",
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"],
          resources: ["arn:aws:logs:*:*:*"]
        })
      ]
    })
    const sourceRole = iam.Role.fromRoleArn(this, "BaseRole", iamRoleArn, {
      mutable: true
    })
    sourceRole.attachInlinePolicy(osCommandInlinePolicy)

    // Define stack-specific name of the IoT thing group
    const groupName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "deployment-group",
      suffix: stackRandom,
      resourceRegex: "a-zA-Z0-9:_-",
      maxLength: 128
    })
    // Create thing group as deployment target and add the thing
    const deploymentGroup = new IotThingGroup(this, "DeploymentGroup", {
      thingGroupName: groupName
    })
    deploymentGroup.addThing(thingArn)

    // Create component(s) for accelerator

    // Reference the base stack's component bucket
    const componentBucket = s3.Bucket.fromBucketArn(this, "ComponentBucket", componentBucketArn)

    // Create OS Command component
    // uses same component file name and path as AWS published components,
    // see the source recipe file for more details
    const componentName = "ggAccel.os_command"
    const componentVersion = "1.0.0"
    const osCommandComponent = new GreengrassV2Component(this, "OsCommandComponent", {
      componentName: componentName,
      componentVersion: componentVersion,
      bucket: componentBucket,
      artifactZipPrefix: `${componentName}/${componentVersion}/`,
      targetArtifactKeyName: `${componentName}.zip`,
      sourceArtifactPath: path.join(__dirname, "..", "components", componentName, "artifacts", componentName, componentVersion),
      sourceRecipeFile: path.join(__dirname, "..", "components", componentName, `${componentName}-${componentVersion}.yaml`)
    })

    // create deployment -- cancel deployment
    const greengrassDeployment = new GreengrassV2Deployment(this, "OsCommandGreengrassDeployment", {
      targetArn: deploymentGroup.thingGroupArn,
      deploymentName: `${this.stackName} - operating system command deployment`,
      component: {
        // accelerator component(s)
        [osCommandComponent.componentName]: {
          componentVersion: osCommandComponent.componentVersion
          // configurationUpdate: {
          //   merge: JSON.stringify({
          //     Message: "Welcome from the Greengrass accelerator stack"
          //   })
          // }
        }
      }
    })

    // Set stack outputs to be consumed by local processes
    new cdk.CfnOutput(this, "RequestTopic", {
      value: `${thingName}/os_cmd/request`
    })
    new cdk.CfnOutput(this, "ResponseTopic", {
      value: `${thingName}/os_cmd/response`
    })

    // ************ End of CDK Constructs / stack - Supporting functions below ************

    function makeid(length: number) {
      // Generate a n-length random value for each resource
      var result = ""
      var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
      var charactersLength = characters.length
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
