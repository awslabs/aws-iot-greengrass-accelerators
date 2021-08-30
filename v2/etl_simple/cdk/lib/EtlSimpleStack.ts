// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as seedrandom from "seedrandom"
import * as cdk from "@aws-cdk/core"
import * as iam from "@aws-cdk/aws-iam"
import * as s3 from "@aws-cdk/aws-s3"
import { IotPolicy } from "../../../os_cmd/cdk/lib/IotPolicy/IotPolicy"
import { IotThingGroup } from "../../../base/cdk/lib/IotThingGroup/IotThingGroup"
import { GreengrassV2Component } from "../../../base/cdk/lib/GreengrassV2Component/GreengrassV2Component"
import { GreengrassV2Deployment } from "../../../base/cdk/lib/GreengrassV2Deployment/GreengrassV2Deployment"

import * as myConst from "./Constants"

export class EtlSimpleStack extends cdk.Stack {
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
    const stackRandom: string = makeid(8, parentStack)
    console.log("random is ", stackRandom)

    // Load parameters from parent stack
    const thingArn = cdk.Fn.importValue(`${parentStack}-ThingArn`)
    const thingName = cdk.Fn.importValue(`${parentStack}-ThingName`)
    const certificateArn = cdk.Fn.importValue(`${parentStack}-CertificateArn`)
    const iamRoleArn = cdk.Fn.importValue(`${parentStack}-IamRoleArn`)
    const componentBucketArn = cdk.Fn.importValue(`${parentStack}-ComponentBucketArn`)

    // Layered constructs - each constructs derived values can be used for subsequent constructs

    // Create IoT policy and attach to certificate
    const etlSimplePolicyName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "gg-accel-etl-simple",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 128
    })
    const iotPolicy = new IotPolicy(this, "EtlSimpleIotPolicy", {
      iotPolicyName: etlSimplePolicyName,
      iotPolicy: myConst.etlSimpleIoTPolicy,
      certificateArn: certificateArn,
      policyParameterMapping: {
        thingname: thingName,
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId")
      }
    })
    // Add an inline policy to the IAM role used by the IoT role alias
    const etlSimpleInlinePolicy = new iam.Policy(this, "EtlSimplePolicy", {
      policyName: "EtlSimpleAccelerator",
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
    sourceRole.attachInlinePolicy(etlSimpleInlinePolicy)

    // Define stack-specific name of the IoT thing group
    const groupName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "deployment-group-etl",
      suffix: stackRandom,
      resourceRegex: "a-zA-Z0-9:_-",
      maxLength: 128
    })
    // Create thing group as deployment target and add the thing
    const deploymentGroup = new IotThingGroup(this, "DeploymentGroupEtl", {
      thingGroupName: groupName
    })
    deploymentGroup.addThing(thingArn)

    // Create component(s) for accelerator

    // Reference the base stack's component bucket
    const componentBucket = s3.Bucket.fromBucketArn(this, "ComponentBucket", componentBucketArn)

    // Create ETL Simple components
    // uses same component file name and path as AWS published components,
    // see the source recipe file for more details
    const etlSimpleExtractComponentName = "ggAccel.etl_simple.extract"
    const etlSimpleExtractComponentVersion = "1.0.0"
    const etlSimpleExtractComponent = new GreengrassV2Component(this, "EtlSimpleExtractComponent", {
      componentName: etlSimpleExtractComponentName,
      componentVersion: etlSimpleExtractComponentVersion,
      bucket: componentBucket,
      artifactZipPrefix: `${etlSimpleExtractComponentName}/${etlSimpleExtractComponentVersion}/`,
      targetArtifactKeyName: `${etlSimpleExtractComponentName}.zip`,
      sourceArtifactPath: path.join(__dirname, "..", "components", etlSimpleExtractComponentName, "artifacts", etlSimpleExtractComponentName, etlSimpleExtractComponentVersion),
      sourceRecipeFile: path.join(__dirname, "..", "components", etlSimpleExtractComponentName, `${etlSimpleExtractComponentName}-${etlSimpleExtractComponentVersion}.json`)
    })
    
    const etlSimpleTransformComponentName = "ggAccel.etl_simple.transform"
    const etlSimpleTransformComponentVersion = "1.0.0"
    const etlSimpleTransformComponent = new GreengrassV2Component(this, "EtlSimpleTransformComponent", {
      componentName: etlSimpleTransformComponentName,
      componentVersion: etlSimpleTransformComponentVersion,
      bucket: componentBucket,
      artifactZipPrefix: `${etlSimpleTransformComponentName}/${etlSimpleTransformComponentVersion}/`,
      targetArtifactKeyName: `${etlSimpleTransformComponentName}.zip`,
      sourceArtifactPath: path.join(__dirname, "..", "components", etlSimpleTransformComponentName, "artifacts", etlSimpleTransformComponentName, etlSimpleTransformComponentVersion),
      sourceRecipeFile: path.join(__dirname, "..", "components", etlSimpleTransformComponentName, `${etlSimpleTransformComponentName}-${etlSimpleTransformComponentVersion}.json`)
    })
    
    const etlSimpleLoadComponentName = "ggAccel.etl_simple.load"
    const etlSimpleLoadComponentVersion = "1.0.0"
    const etlSimpleLoadComponent = new GreengrassV2Component(this, "EtlSimpleLoadComponent", {
      componentName: etlSimpleLoadComponentName,
      componentVersion: etlSimpleLoadComponentVersion,
      bucket: componentBucket,
      artifactZipPrefix: `${etlSimpleLoadComponentName}/${etlSimpleLoadComponentVersion}/`,
      targetArtifactKeyName: `${etlSimpleLoadComponentName}.zip`,
      sourceArtifactPath: path.join(__dirname, "..", "components", etlSimpleLoadComponentName, "artifacts", etlSimpleLoadComponentName, etlSimpleLoadComponentVersion),
      sourceRecipeFile: path.join(__dirname, "..", "components", etlSimpleLoadComponentName, `${etlSimpleLoadComponentName}-${etlSimpleLoadComponentVersion}.json`)
    })

    // create deployment -- cancel deployment
    const greengrassDeployment = new GreengrassV2Deployment(this, "EtlSimpleDeployment", {
      targetArn: deploymentGroup.thingGroupArn,
      deploymentName: `${this.stackName} - extract transform load deployment`,
      component: {
        // accelerator component(s)
        [etlSimpleExtractComponent.componentName]: {
          componentVersion: etlSimpleExtractComponent.componentVersion
        },
        [etlSimpleTransformComponent.componentName]: {
          componentVersion: etlSimpleTransformComponent.componentVersion
        },
        [etlSimpleLoadComponent.componentName]: {
          componentVersion: etlSimpleLoadComponent.componentVersion
        }
      }
    })

    // Set stack outputs to be consumed by local processes
    new cdk.CfnOutput(this, "CloudPublishTopic", {
      value: `${thingName}/etl_simple/load`
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
