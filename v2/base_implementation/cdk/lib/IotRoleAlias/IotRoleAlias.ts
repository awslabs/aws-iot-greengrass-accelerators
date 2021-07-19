// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"

/**
 * @summary The properties for the IotRoleAlias class.
 */
export interface IotRoleAliasProps {
  /**
   * Base AWS IoT role alias name.
   *
   * @default - None
   */
  readonly iotRoleAliasName: string
  /**
   * Optional base IAM Role name.
   *
   * @default - `roleAliasName` value is used.
   */
  readonly iamRoleName?: string
  /**
   * IAM policy document to apply (inline) to the IAM role.
   *
   * @default - None
   */
  readonly iamPolicy: iam.PolicyDocument
  /**
   * Optional name of the default inline policy created on the IAM role.
   *
   * @default -"DefaultPolicyForRoleAlias"
   */
  readonly iamPolicyName?: string
}

/**
 * This construct creates an AWS IoT role alias based upon a provided IAM
 * policy that will be attached to an associated IAM role.
 *
 * @summary Creates an AWS IoT role alias and referenced IAM role with provided IAM policy.
 */

/**
 * @summary The IotRoleAlias class.
 */

export class IotRoleAlias extends cdk.Construct {
  public readonly iamRoleArn: string
  public readonly roleAliasName: string
  public readonly roleAliasArn: string

  private customResourceName = "IotRoleAliasFunction"

  /**
   *
   * @summary Constructs a new instance of the IotRoleAlias class.
   * @param {cdk.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {IotRoleAliasProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: cdk.Construct, id: string, props: IotRoleAliasProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName

    // Validate and derive final values for resources
    const inlinePolicyName = props.iamPolicyName || "DefaultPolicyForIotRoleAlias"
    const iamRoleName = props.iamRoleName || props.iotRoleAliasName

    // IAM Role name (64 max, regex: [^_+=,.@-], add 8 random id at end)
    let completeIamRoleName = `${stackName}-${iamRoleName.replace(/[^\w+=,.@-]/g, "")}`
    completeIamRoleName = `${completeIamRoleName.substring(0, 55)}-${makeid(8)}`

    // IoT role alias name (128 max, [\w=,@-], add 8 random id at end)
    let completeIoTRoleAliasName = `${stackName}-${props.iotRoleAliasName.replace(/[^\w=,@-]/g, "")}`
    completeIoTRoleAliasName = `${completeIoTRoleAliasName.substring(0, 119)}-${makeid(8)}`

    // Create IAM role with permissions
    const iamRole = new iam.Role(this, "IamRole", {
      roleName: completeIamRoleName,
      assumedBy: new iam.ServicePrincipal("credentials.iot.amazonaws.com"),
      description: "Allow Greengrass token exchange service to obtain temporary credentials",
      inlinePolicies: {
        [inlinePolicyName]: props.iamPolicy
      }
    })

    const provider = IotRoleAlias.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        StackName: stackName,
        IotRoleAliasName: completeIoTRoleAliasName,
        IamRoleArn: iamRole.roleArn
      }
    })

    // Custom resource Lambda role permissions
    // Permissions for the IAM role created/deleted
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
    // Permissions for the IoT role alias created/deleted
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreateRoleAlias", "iot:DeleteRoleAlias"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref("AWS::AccountId")}:rolealias/${completeIoTRoleAliasName}`
        ]
      })
    )

    // class public values
    this.iamRoleArn = iamRole.roleArn
    this.roleAliasName = completeIoTRoleAliasName
    this.roleAliasArn = `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref(
      "AWS::AccountId"
    )}:rolealias/${completeIoTRoleAliasName}`

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
  }

  // Separate static function to create or return singleton provider
  static getOrCreateProvider = (scope: cdk.Construct, resourceName: string): cr.Provider => {
    const stack = cdk.Stack.of(scope)
    const uniqueId = resourceName
    const existing = stack.node.tryFindChild(uniqueId) as cr.Provider

    if (existing === undefined) {
      const createThingFn = new lambda.Function(stack, `${uniqueId}-Provider`, {
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(1),
        handler: "role_alias.handler",
        code: lambda.Code.fromAsset(path.join(__dirname, "assets"))
      })
      // Role permissions are handled by the main constructor

      // Create the provider that invokes the Lambda function
      const createThingProvider = new cr.Provider(stack, uniqueId, {
        onEventHandler: createThingFn,
        logRetention: logs.RetentionDays.ONE_DAY
      })
      return createThingProvider
    } else {
      // Second or additional call, use existing provider
      return existing
    }
  }
}
