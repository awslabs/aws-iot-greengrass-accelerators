// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from "@aws-cdk/core"
import * as iam from "@aws-cdk/aws-iam"
import { IotThingCertPolicy } from "./IotThingCertPolicy/IotThingCertPolicy"
import { IotRoleAlias } from "./IotRoleAlias/IotRoleAlias"
import { IotThingGroup } from "./IotThingGroup/IotThingGroup"
import * as myConst from "./Constants"

export class BaseImplementationStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // Layered constructs - each constructs derived values can be used for subsequent constructs
    // suffix to use for all stack resources to make unique
    // In this stack all resources will use the format STACKNAME-RESOURCENAME-RANDOMSUFFIX
    const stackRandom: string = makeid(8)

    // Create IoT role alias
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
        })
      ]
    })

    // Create IoT role alias
    const roleAliasName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "GreengrassV2TokenExchangeRole",
      suffix: stackRandom,
      resourceRegex: "\\w=,@-",
      maxLength: 128
    })
    const iamRoleName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "RoleForIoTRoleAlias",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 64
    })
    const greengrassRoleAlias = new IotRoleAlias(this, "IoTRoleAlias", {
      iotRoleAliasName: roleAliasName,
      iamRoleName: iamRoleName,
      iamPolicy: greengrassRoleMinimalPolicy
    })

    // IoT thing, certificate/private key, and IoT Policy
    const greengrassCoreThingName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "greengrass-core",
      suffix: stackRandom,
      resourceRegex: "a-zA-Z0-9:_-",
      maxLength: 128
    })
    const greengrassCoreIotPolicyName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "greengrass-minimal-policy",
      suffix: stackRandom,
      resourceRegex: "\\w+=,.@-",
      maxLength: 128
    })
    const iotThingCertPol = new IotThingCertPolicy(this, "GreengrassCore", {
      thingName: greengrassCoreThingName,
      iotPolicyName: greengrassCoreIotPolicyName,
      iotPolicy: myConst.greengrassCoreMinimalIoTPolicy,
      policyParameterMapping: {
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId"),
        rolealiasname: greengrassRoleAlias.roleAliasName
      }
    })
    new cdk.CfnOutput(this, "OutputThingArn", {
      // exportName: "ThingArn",
      value: iotThingCertPol.thingArn
    })
    new cdk.CfnOutput(this, "CertificatePemParameter", {
      // exportName: "CertificatePemParameter",
      value: iotThingCertPol.certificatePemParameter
    })
    new cdk.CfnOutput(this, "PrivateKeySecretParameter", {
      // exportName: "PrivateKeySecretParameter",
      value: iotThingCertPol.privateKeySecretParameter
    })
    new cdk.CfnOutput(this, "DataAtsEndpointAddress", {
      // exportName: "DataAtsEndpointAddress",
      value: iotThingCertPol.dataAtsEndpointAddress
    })

    // Create thing group and add thing
    const groupName = fullResourceName({
      stackName: cdk.Stack.of(this).stackName,
      baseName: "greengrass-deployment-group",
      suffix: stackRandom,
      resourceRegex: "a-zA-Z0-9:_-",
      maxLength: 128
    })
    const deploymentGroup = new IotThingGroup(this, "DeploymentGroup", {
      thingGroupName: groupName
    })
    deploymentGroup.addThing(iotThingCertPol.thingArn)

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
