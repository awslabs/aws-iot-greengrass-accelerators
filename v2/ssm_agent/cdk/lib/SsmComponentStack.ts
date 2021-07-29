// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as iam from "@aws-cdk/aws-iam"
import * as s3 from "@aws-cdk/aws-s3"
import { IotPolicy } from "./IotPolicy/IotPolicy"
import { IotThingGroup } from "../../../base/cdk/lib/IotThingGroup/IotThingGroup"
import { GreengrassV2Component } from "../../../base/cdk/lib/GreengrassV2Component/GreengrassV2Component"
import * as myConst from "./Constants"

export class SsmComponentStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    if (cdk.Stack.of(this).stackName.length > 20) {
      console.error("Stack name must be less than 20 characters in length")
      process.exitCode = 1
    }
    const parentStack = this.node.tryGetContext("baseStack")

    // suffix to use for all stack resources to make unique
    // In this stack all resources will use the format STACKNAME-RESOURCENAME-RANDOMSUFFIX
    const stackRandom: string = makeid(8)

    // Load parameters from parent stack
    const thingArn = cdk.Fn.importValue(`${parentStack}-ThingArn`)
    const certificateArn = cdk.Fn.importValue(`${parentStack}-CertificateArn`)
    const iamRoleArn = cdk.Fn.importValue(`${parentStack}-IamRoleArn`)
    const componentBucketArn = cdk.Fn.importValue(`${parentStack}-ComponentBucketArn`)

    // Layered constructs - each constructs derived values can be used for subsequent constructs

    // Create IoT policy and attach to certificate
    const ssmAgentPolicyName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "ssm-agent-component",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 128
    })
    const iotPolicy = new IotPolicy(this, "SsmIoTPolicy", {
      iotPolicyName: ssmAgentPolicyName,
      iotPolicy: myConst.ssmAgentIoTPolicy,
      certificateArn: certificateArn,
      policyParameterMapping: {
        thingname: thingArn.split("/").slice(-1)[0],
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId")
      }
    })
    // Add an inline policy to the IAM role used by the IoT role alias
    const ssmAgentInlinePolicy = new iam.Policy(this, "SsmAgentPolicy", {
      policyName: "SsmAgentAccelerator",
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["ssm:*"],
          resources: ["*"]
        })
      ]
    })
    const sourceRole = iam.Role.fromRoleArn(this, "SourceRole", iamRoleArn, {
      mutable: true
    })
    sourceRole.attachInlinePolicy(ssmAgentInlinePolicy)

    // Define stack-specific name of the IoT thing group
    const groupName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "ssm-agent-accelerator",
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

    const componentName = "ggAccel.ssm_agent"
    const componentVersion = "1.0.0"
    const helloWorldComponent = new GreengrassV2Component(this, "SsmAgentComponent", {
      componentName: componentName,
      componentVersion: componentVersion,
      bucket: componentBucket,
      sourceArtifactPath: path.join(__dirname, "..", "components", componentName, "artifacts", componentName, componentVersion),
      sourceRecipeFile: path.join(__dirname, "..", "components", componentName, `${componentName}-${componentVersion}.yaml`)
      // Optional URI demonstrating user defined key name and path
      // targetArtifactKeyName: `path1/path2/${componentName}-${componentVersion}.zip`
    })

    // create deployment -- cancel deployment

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
