// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"
import { Construct } from "@aws-cdk/core"

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

    const provider = IotRoleAlias.getOrCreateProvider(this, completeIamRoleName)

    const customResource = new cdk.CustomResource(this, "IoTCreateThingCertPolicy", {
      serviceToken: provider.serviceToken,
      properties: {
        StackName: props.stackName,
        IamRoleName: completeIamRoleName,
        IamPolicy: props.iamPolicy,
        IotRoleAliasName: completeIoTRoleAliasName,
        PolicyName: inlinePolicyName
      }
    })

    // Add resource-specific permissions to the Lambda role policy
    // IAM related on roles
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:DeleteRolePolicy",
          "iam:DetachRolePolicy",
          "iam:ListAttachedRolePolicies",
          "iam:ListRolePolicies",
          "iam:PassRole", // Needed to associate IAM role with alias role
          "iam:PutRolePolicy"
        ],
        resources: [`arn:${cdk.Fn.ref("AWS::Partition")}:iam::${cdk.Fn.ref("AWS::AccountId")}:role/${completeIamRoleName}`]
      })
    )
    // IoT role alias
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreateRoleAlias", "iot:DeleteRoleAlias"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref("AWS::AccountId")}:rolealias/${completeIoTRoleAliasName}`
        ]
      })
    )

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

    // Set resource return values from function
    this.iamRoleArn = customResource.getAttString("IamRoleArn")
  }
  static getOrCreateProvider = (scope: cdk.Construct, roleName: string): cr.Provider => {
    const stack = cdk.Stack.of(scope)
    const uniqueId = "CreateIoTRoleAlias"
    const existing = stack.node.tryFindChild(uniqueId) as cr.Provider

    if (existing === undefined) {
      const createThingFn = new lambda.Function(stack, `${uniqueId}Provider`, {
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(1),
        handler: "role_alias.handler",
        code: lambda.Code.fromAsset(path.join(__dirname, "assets"))
      })
      // Role permissions are handled by the main constructor

      // Provider that invokes the Lambda function
      const createThingProvider = new cr.Provider(stack, uniqueId, {
        onEventHandler: createThingFn,
        logRetention: logs.RetentionDays.ONE_DAY
      })
      return createThingProvider
    } else {
      return existing
    }
  }
}
