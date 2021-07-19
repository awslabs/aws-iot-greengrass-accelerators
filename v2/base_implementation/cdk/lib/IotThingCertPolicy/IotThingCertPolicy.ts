// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as _ from "lodash"
import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"
import { PythonFunction } from "@aws-cdk/aws-lambda-python"

/**
 * @summary The properties for the IotThingCertPolicy class.
 */
export interface IotThingCertPolicyProps {
  /**
   * Name of AWS IoT thing to create.
   *
   * @default - None
   */
  thingName: string
  /**
   * The AWS IoT policy to be created and attached to the certificate.
   * JSON string converted to IoT policy, lodash format for replacement.
   *
   * @default - None
   */
  iotPolicy: string
  /**
   * An object of parameters and values to be replaced if a Jinja template is
   * provided. For each matching parameter in the policy template, the value
   * will be used.
   *
   * @default - None
   */
  policyParameterMapping?: object
}

/**
 * This construct creates an AWS IoT thing, IoT certificate, and IoT policy.
 * It attaches the certificate to the thing and policy, and stores the
 * certificate private key into an AWS Systems Manager Parameter Store
 * string for reference outside of the CloudFormation stack.
 *
 * Use this construct to create and delete a thing, principal, and policy for
 * testing or other singular uses.
 *
 * @summary Creates and associates an AWS IoT thing, certificate and policy.
 *
 */

/**
 * @ summary The IotThingCertPolicy class.
 */

export class IotThingCertPolicy extends cdk.Construct {
  public readonly thingArn: string
  public readonly certificateArn: string
  public readonly certificatePem: string
  public readonly privateKeySecretArn: string
  private customResourceName = "IotThingCertPolicyFunction"

  /**
   * @summary Constructs a new instance of the IotThingCertPolicy class.
   * @param {cdp.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {IotThingCertPolicyProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: cdk.Construct, id: string, props: IotThingCertPolicyProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName
    // Validate and derive final values for resources
    let completeIotThingName = `${stackName}-${props.thingName.replace(/[^\[a-zA-Z0-9:_-]]/g, "")}`
    completeIotThingName = `${completeIotThingName.substring(0, 119)}-${makeid(8)}`
    let completePolicyName = `${stackName}-${props.thingName.replace(/[^[\w+=,.@-]]/g, "")}`
    completePolicyName = `${completePolicyName.substring(0, 119)}-${makeid(8)}`

    var policyTemplate = _.template(props.iotPolicy)
    var iotPolicy = policyTemplate(props.policyParameterMapping)

    const provider = IotThingCertPolicy.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        StackName: stackName,
        ThingName: completeIotThingName,
        IotPolicy: iotPolicy,
        IoTPolicyName: completePolicyName
      }
    })

    // Custom resource Lambda role permissions
    // Permissions to act on thing, certificate, and policy
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreateThing", "iot:DeleteThing"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref("AWS::AccountId")}:thing/${completeIotThingName}`
        ]
      })
    )

    // Create and delete specific policy
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreatePolicy", "iot:DeletePolicy", "iot:DeletePolicyVersion", "iot:ListPolicyVersions", "iot:ListTargetsForPolicy"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref("AWS::AccountId")}:policy/${completePolicyName}`
        ]
      })
    )

    // Actions without resource types
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "iot:AttachPolicy",
          "iot:AttachThingPrincipal",
          "iot:CreateCertificateFromCsr",
          "iot:DeleteCertificate",
          "iot:DetachPolicy",
          "iot:DetachThingPrincipal",
          "iot:ListAttachedPolicies",
          "iot:ListPrincipalThings",
          "iot:ListThingPrincipals",
          "iot:UpdateCertificate"
        ],
        resources: ["*"]
      })
    )

    // class public values
    this.certificatePem = customResource.getAttString("CertificatePem")
    this.privateKeySecretArn = customResource.getAttString("PrivateKeySecretArn")
    this.thingArn = customResource.getAttString("ThingArn").toString()
    this.certificateArn = customResource.getAttString("CertificateArn")

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
      // const createThingFn = new lambda.Function(stack, `${uniqueId}-Provider`, {
      //   runtime: lambda.Runtime.PYTHON_3_8,
      //   timeout: cdk.Duration.minutes(1),
      //   handler: "thing_cert_policy.handler",
      //   code: lambda.Code.fromAsset(path.join(__dirname, "assets"))
      // })
      const createThingFn = new PythonFunction(stack, `${uniqueId}-Provider`, {
        entry: path.join(__dirname, "assets"),
        index: "thing_cert_policy.py",
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(1)
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
