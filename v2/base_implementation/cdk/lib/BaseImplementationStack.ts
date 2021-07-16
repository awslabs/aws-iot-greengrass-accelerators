// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as cdk from "@aws-cdk/core"
import * as iam from "@aws-cdk/aws-iam"
import { IotCreateThingCertPolicy } from "./IotCreateThingCertPolicy/IotCreateThingCertPolicy"
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

    // // testing what two calls looks like
    // const test = new IotRoleAlias(this, "IoTRoleAlias2", {
    //   iotRoleAliasName: "GreengrassV2TokenExchangeRoleNumber2",
    //   iamRoleName: "my_other_role",
    //   iamPolicy: myConst.greengrassMinimalRoleAliasPolicy
    // })

    // IoT thing, certificate/private key, and IoT Policy

    // const iotThingCertPol = new IotCreateThingCertPolicy(this, "CreateIoTThing", {
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
