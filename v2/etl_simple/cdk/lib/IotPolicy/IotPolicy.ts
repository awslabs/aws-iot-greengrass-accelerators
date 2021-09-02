// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// In its current form, this code is not fit for production workloads.

import * as _ from "lodash"
import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"

export interface Mapping {
  [keys: string]: string
}

/**
 * @summary The properties for the IotPolicyProps class.
 */
export interface IotPolicyProps {
  /**
   * Name of the AWS IoT Core policy to create.
   *
   * @default - None
   */
  iotPolicyName: string
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
  /**
   * Certificate Arn to which to attach the policy
   *
   * @default - None
   */
  certificateArn?: string
}

/**
 * This construct creates an IoT policy and optionally attaches it to
 * an existing IoT certificate principal.
 *
 * @summary Creates an AWS IoT policy and optionally attached it to a certificate.
 *
 */

/**
 * @ summary The IotThingCertPolicy class.
 */

export class IotPolicy extends cdk.Construct {
  public readonly thingArn: string
  public readonly iotPolicyArn: string
  public readonly certificateArn: string
  public readonly certificatePemParameter: string
  public readonly privateKeySecretParameter: string
  public readonly dataAtsEndpointAddress: string
  public readonly credentialProviderEndpointAddress: string
  private customResourceName = "IotPolicyFunction"

  /**
   * @summary Constructs a new instance of the IotPolicy class.
   * @param {cdp.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {IotPolicyProps} props - user provided props for the construct.
   * @since 1.116.0
   */
  constructor(scope: cdk.Construct, id: string, props: IotPolicyProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName
    // Validate and derive final values for resources

    // For the AWS Core policy, the template maps replacements from the
    // props.policyParameterMapping along with the following provided variables:
    var policyTemplate = _.template(props.iotPolicy)
    var iotPolicy = policyTemplate(props.policyParameterMapping)

    const provider = IotPolicy.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        StackName: stackName,
        IotPolicy: iotPolicy,
        IoTPolicyName: props.iotPolicyName,
        CertificateArn: props.certificateArn
      }
    })

    // Custom resource Lambda role permissions
    // Create and delete specific policy
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreatePolicy", "iot:DeletePolicy", "iot:DeletePolicyVersion", "iot:ListPolicyVersions", "iot:ListTargetsForPolicy"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref("AWS::AccountId")}:policy/${props.iotPolicyName}`
        ]
      })
    )
    // Actions without resource types
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:AttachPolicy", "iot:DetachPolicy", "iot:ListAttachedPolicies", "iot:UpdateCertificate"],
        resources: ["*"]
      })
    )

    // class public values
    this.iotPolicyArn = customResource.getAttString("IotPolicyArn")
  }

  // Separate static function to create or return singleton provider
  static getOrCreateProvider = (scope: cdk.Construct, resourceName: string): cr.Provider => {
    const stack = cdk.Stack.of(scope)
    const uniqueId = resourceName
    const existing = stack.node.tryFindChild(uniqueId) as cr.Provider

    if (existing === undefined) {
      const createThingFn = new lambda.Function(stack, `${uniqueId}-Provider`, {
        handler: "iot_policy.handler",
        code: lambda.Code.fromAsset(path.join(__dirname, "assets")),
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(1),
        logRetention: logs.RetentionDays.ONE_MONTH
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
