// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from "@aws-cdk/core"
import * as iam from "@aws-cdk/aws-iam"
import { IotThingCertPolicy } from "./IotThingCertPolicy/IotThingCertPolicy"
import { IotRoleAlias } from "./IotRoleAlias/IotRoleAlias"
import * as myConst from "./Constants"

export class BaseImplementationStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // Layered constructs - each constructs derived values can be used for subsequent constructs

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

    const greengrassRoleAlias = new IotRoleAlias(this, "IoTRoleAlias", {
      iotRoleAliasName: "GreengrassV2TokenExchangeRole",
      iamRoleName: "RoleAliasForGreengrassCore",
      iamPolicy: greengrassRoleMinimalPolicy
    })

    // IoT thing, certificate/private key, and IoT Policy

    const iotThingCertPol = new IotThingCertPolicy(this, "GreengrassCore", {
      thingName: "greengrass-core",
      iotPolicy: myConst.greengrassCoreMinimalIoTPolicy,
      policyParameterMapping: {
        thingname: "greengrass-core",
        region: cdk.Fn.ref("AWS::Region"),
        account: cdk.Fn.ref("AWS::AccountId"),
        rolealiasname: greengrassRoleAlias.roleAliasName
      }
    })
    const output1 = new cdk.CfnOutput(this, "test", {
      exportName: "foo",
      value: iotThingCertPol.thingArn
    })

    // const iotThingCertPol = new IotThingCertPolicy(this, "CreateIoTThing", {
    //   stackName: id,
    //   thingName: "foo-test",
    //   createCertificate: true,
    //   iotPolicy: {
    //     Version: "2012-10-17",
    //     Statement: [
    //       { Effect: "Allow", Action: "iot:*", Resource: "*" },
    //       { Effect: "Allow", Action: "greengrass:*", Resource: "*" }
    //     ]
    //   }
    // })
  }
}
