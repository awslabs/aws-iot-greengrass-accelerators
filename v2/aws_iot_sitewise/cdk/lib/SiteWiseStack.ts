// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as os from "os"
import * as seedrandom from "seedrandom"
import { Construct } from "constructs"
import * as cdk from "aws-cdk-lib"
import { aws_iam as iam } from "aws-cdk-lib"
import { IotPolicy } from "@cdkConstructs/IotPolicy"
import { IotThingGroup } from "@cdkConstructs/IotThingGroup"
import { GreengrassV2Deployment } from "@cdkConstructs/GreengrassV2Deployment"
import { aws_iotsitewise as sitewise } from "aws-cdk-lib"

import * as myConst from "./Constants"
import { SampleAssetModel } from "./SampleAssetModel"
import { SampleAsset } from "./SampleAsset"

export class SiteWiseStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    if (cdk.Stack.of(this).stackName.length > 20) {
      console.error("Stack name must be less than 20 characters in length")
      process.exitCode = 1
    }

    const parentStack = this.node.tryGetContext("baseStack")

    if (parentStack === undefined) {
      console.error(
        "\x1b[31m%s\x1b[0m",
        'Parent stack must be provided with --context baseStack="gg-accel-base" argument for "cdk deploy" or "cdk destroy"'
      )
      process.exitCode = 1
    }

    // suffix to use for all stack resources to make unique
    // In this stack all resources will use the format STACKNAME-RESOURCENAME-RANDOMSUFFIX
    const stackRandom: string = makeid(8, parentStack)
    const hostname: string = os.hostname()

    // Load parameters from parent stack
    const thingArn = cdk.Fn.importValue(`${parentStack}-ThingArn`)
    const thingName = cdk.Fn.importValue(`${parentStack}-ThingName`)
    const certificateArn = cdk.Fn.importValue(`${parentStack}-CertificateArn`)
    const iamRoleArn = cdk.Fn.importValue(`${parentStack}-IamRoleArn`)

    // Additional local parameters and conditions
    const opcUaEndpoint = new cdk.CfnParameter(this, "opcUaEndpoint", {
      type: "String",
      description:
        "The OPC-UA endpoint to be used by the AWS IoT SiteWise gateway.",
      default: `opc.tcp://${hostname}:26543`
    })
    const deploySampleAssetModel = new cdk.CfnParameter(
      this,
      "deploySampleAssetModel",
      {
        type: "String",
        allowedValues: ["true", "false"],
        description:
          "Whether to deploy the sample asset model to the AWS IoT SiteWise gateway.",
        default: "true"
      }
    )
    const deploySampleAssetModelCondition = new cdk.CfnCondition(
      this,
      "DeploySampleAssetModelCondition",
      {
        expression: cdk.Fn.conditionEquals(
          deploySampleAssetModel.valueAsString,
          "true"
        )
      }
    )

    // Layered constructs - each constructs derived values can be used for subsequent constructs

    // Create IoT policy and attach to certificate
    const siteWisePolicyName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "gg-accel-sitewise",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 128
    })

    const iotPolicy = new IotPolicy(this, "SiteWiseIotPolicy", {
      iotPolicyName: siteWisePolicyName,
      iotPolicy: myConst.siteWiseIoTPolicy,
      certificateArn: certificateArn,
      policyParameterMapping: {
        thingname: thingName,
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId")
      }
    })

    // Add an inline policy to the IAM role used by the IoT role alias
    const siteWiseInlinePolicy = new iam.Policy(this, "SiteWisePolicy", {
      policyName: "SiteWiseAccelerator",
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["iotsitewise:BatchPutAssetPropertyValue"],
          resources: ["*"]
        })
      ]
    })

    const sourceRole = iam.Role.fromRoleArn(this, "BaseRole", iamRoleArn, {
      mutable: true
    })

    sourceRole.attachInlinePolicy(siteWiseInlinePolicy)

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

    // create deployment -- cancel deployment
    const greengrassDeployment = new GreengrassV2Deployment(
      this,
      "SiteWiseGreengrassDeployment",
      {
        targetArn: deploymentGroup.thingGroupArn,
        deploymentName: `${this.stackName} - AWS IoT SiteWise deployment`,
        component: {
          "aws.iot.SiteWiseEdgeCollectorOpcua": { componentVersion: "2.4.1" },
          "aws.iot.SiteWiseEdgePublisher": { componentVersion: "3.1.1" },
          "aws.greengrass.StreamManager": { componentVersion: "2.1.12" }
        }
      }
    )

    // Sample asset models and x2 assets to match local OPC-UA demo server
    const sampleAssetModel = new SampleAssetModel(this, "SampleAssetModel", {
      condition: deploySampleAssetModelCondition
    })

    const sampleAsset1 = new SampleAsset(this, "SampleAsset1", {
      assetModelId: sampleAssetModel.ref,
      assetName: "East Wing Fan",
      propertyAlias: "/AnyCompany/1/Generator/FanSpeed",
      condition: deploySampleAssetModelCondition
    })

    const sampleAsset2 = new SampleAsset(this, "SampleAsset2", {
      assetModelId: sampleAssetModel.ref,
      assetName: "West Wing Fan",
      propertyAlias: "/AnyCompany/2/Generator/FanSpeed",
      condition: deploySampleAssetModelCondition
    })

    // AWS IoT SiteWise gateway
    const siteWiseGw = new sitewise.CfnGateway(this, "SitewiseGateway", {
      gatewayName: `${this.stackName}-Gateway`,
      gatewayPlatform: {
        greengrassV2: {
          coreDeviceThingName: thingName
        }
      },
      gatewayCapabilitySummaries: [
        {
          capabilityNamespace: "iotsitewise:opcuacollector:2",
          capabilityConfiguration: JSON.stringify({
            sources: [
              {
                name: "OPCUAServer",
                endpoint: {
                  certificateTrust: { type: "TrustAny" },
                  endpointUri: opcUaEndpoint.valueAsString,
                  securityPolicy: "NONE",
                  messageSecurityMode: "NONE",
                  identityProvider: { type: "Anonymous" },
                  nodeFilterRules: []
                },
                measurementDataStreamPrefix: ""
              }
            ]
          })
        },
        {
          capabilityNamespace: "iotsitewise:publisher:2",
          capabilityConfiguration: JSON.stringify({
            SiteWisePublisherConfiguration: {
              publishingOrder: "TIME_ORDER"
            }
          })
        }
      ]
    })

    siteWiseGw.node.addDependency(greengrassDeployment)

    // ************ End of CDK Constructs / stack - Supporting functions below ************

    function makeid(length: number, seed: string) {
      // Generate a n-length random value for each resource
      var result = ""
      var characters =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
      var charactersLength = characters.length
      seedrandom(seed, { global: true })
      for (var i = 0; i < length; i++) {
        result += characters.charAt(
          Math.floor(Math.random() * charactersLength)
        )
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

    function fullResourceName({
      stackName,
      baseName,
      suffix,
      resourceRegex,
      maxLength
    }: ResourceName) {
      let re = new RegExp(`[^\\[${resourceRegex}]`, "g")
      let resourceName = `${stackName}-${baseName}`.replace(re, "")
      resourceName = resourceName.substring(0, maxLength - suffix.length - 1)
      resourceName = `${resourceName}-${suffix}`
      return resourceName
    }
  }
}
