// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"

/**
 * @summary The properties for the IotCreateThingCertPolicy class.
 */
export interface IotRoleAliasProps {
  /**
   * Name of CloudFormation stack used as part of role alias name
   */
  stackName: string
  /** Name of AWS IoT role alias to create */
  iotRoleAliasName: string
  /** IAM Role name to create */
  iamRoleName: string
  /** IAM policy to apply (inline) to the IAM role */
  iamPolicy: object
  /** Name to assign the default inline policy */
  iamPolicyName?: string
}

export class IotRoleAlias extends cdk.Construct {
  public readonly iamRoleArn: string
  public readonly roleAliasName: string

  constructor(scope: cdk.Construct, id: string, props: IotRoleAliasProps) {
    super(scope, id)

    // Validate and derive final values for resources
    const inlinePolicyName = props.iamPolicyName || "DefaultPolicyForRoleAlias"

    // IAM Role name (64 max, regex: [^_+=,.@-], add 8 random id at end)
    // myStack-this_is_my_text-ABCxyz12
    let completeIamRoleName = `${props.stackName}-${props.iamRoleName.replace(/[^\w+=,.@-]/g, "")}`
    completeIamRoleName = `${completeIamRoleName.substring(0, 55)}-${makeid(8)}`

    // IoT role alias name (128 max, [\w=,@-], add 8 random id at end)
    let completeIoTRoleAliasName = `${props.stackName}-${props.iotRoleAliasName.replace(/[^\w=,@-]/g, "")}`
    completeIoTRoleAliasName = `${completeIoTRoleAliasName.substring(0, 119)}-${makeid(8)}`

    const createThingFn = new lambda.Function(this, "MyHandler", {
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.minutes(1),
      handler: "role_alias.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "assets"))
    })
    // Add permissions for AWS calls within the Lambda function
    if (createThingFn.role) {
      createThingFn.role.addToPrincipalPolicy(
        new iam.PolicyStatement({
          actions: [
            "iam:CreateRole",
            "iam:DeleteRole",
            "iam:DeleteRolePolicy",
            "iam:DetachRolePolicy",
            "iam:ListAttachedRolePolicies",
            "iam:ListRolePolicies",
            "iam:PutRolePolicy",
            "iot:CreateRoleAlias",
            "iot:DeleteRoleAlias"
          ],
          resources: ["*"]
        })
      )
      createThingFn.role.addToPrincipalPolicy(
        new iam.PolicyStatement({
          actions: [
            "iam:PassRole" // !!! Needed to associate IAM role with alias role
          ],
          resources: [`arn:${cdk.Fn.ref("AWS::Partition")}:iam::${cdk.Fn.ref("AWS::AccountId")}:role/${completeIamRoleName}`]
        })
      )
    }

    // Provider that invokes the Lambda function
    const createThingProvider = new cr.Provider(this, "IoTCreateThing", {
      onEventHandler: createThingFn,
      logRetention: logs.RetentionDays.ONE_DAY
    })
    const customResource = new cdk.CustomResource(this, "IoTCreateThingCertPolicy", {
      serviceToken: createThingProvider.serviceToken,
      properties: {
        StackName: props.stackName,
        IamRoleName: completeIamRoleName,
        IamPolicy: props.iamPolicy,
        IotRoleAliasName: completeIoTRoleAliasName,
        PolicyName: inlinePolicyName
      }
    })

    function makeid(length: number) {
      var result = ""
      var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
      var charactersLength = characters.length
      for (var i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength))
      }
      return result
    }

    // Set resource return values from function
    this.iamRoleArn = customResource.getAttString("IamRoleArn")
  }
}
