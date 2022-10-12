// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as _ from "lodash"
import * as path from "path"
import * as cdk from "aws-cdk-lib"
import * as logs from "aws-cdk-lib/aws-logs"
import * as iam from "aws-cdk-lib/aws-iam"
import * as cr from "aws-cdk-lib/custom-resources"
import * as lambda from "aws-cdk-lib/aws-lambda"
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha"
import { Construct } from "constructs"

export interface Mapping {
  [keys: string]: string
}

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
   * will be used. If not provided, only the `<% thingname %>` mapping will be available for the `iotPolicy` template.
   *
   * @default - None
   */
  policyParameterMapping?: Mapping
  /**
   * Selects RSA or ECC private key and certificate generation. If not provided, `RSA` will be used.
   *
   * @default - RSA
   */
  encryptionAlgorithm?: string
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

export class IotThingCertPolicy extends Construct {
  public readonly thingArn: string
  public readonly iotPolicyArn: string
  public readonly certificateArn: string
  public readonly certificatePemParameter: string
  public readonly privateKeySecretParameter: string
  public readonly dataAtsEndpointAddress: string
  public readonly credentialProviderEndpointAddress: string
  private customResourceName = "IotThingCertPolicyFunction"

  /**
   * @summary Constructs a new instance of the IotThingCertPolicy class.
   * @param {cdp.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {IotThingCertPolicyProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: Construct, id: string, props: IotThingCertPolicyProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName
    // Validate and derive final values for resources
    const encryptionAlgorithm = props.encryptionAlgorithm || "RSA"
    if (!["RSA", "ECC"].includes(encryptionAlgorithm)) {
      console.error(
        "Invalid value for encryptionAlgorithm, use either 'RSA' or 'ECC'."
      )
      process.exitCode = 1
    }

    // For the AWS Core policy, the template maps replacements from the
    // props.policyParameterMapping along with the following provided variables:
    // thingname  - used as: <% thingname %>
    let policyParameters = props.policyParameterMapping || {}
    policyParameters.thingname = props.thingName

    // lodash that creates template then applies the mapping
    var policyTemplate = _.template(props.iotPolicy)
    var iotPolicy = policyTemplate(policyParameters)

    const provider = IotThingCertPolicy.getOrCreateProvider(
      this,
      this.customResourceName
    )
    const customResource = new cdk.CustomResource(
      this,
      this.customResourceName,
      {
        serviceToken: provider.serviceToken,
        properties: {
          StackName: stackName,
          ThingName: props.thingName,
          IotPolicy: iotPolicy,
          IoTPolicyName: props.iotPolicyName,
          EncryptionAlgorithm: encryptionAlgorithm,
        },
      }
    )

    // Custom resource Lambda role permissions
    // Permissions to act on thing, certificate, and policy
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreateThing", "iot:DeleteThing"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref(
            "AWS::Region"
          )}:${cdk.Fn.ref("AWS::AccountId")}:thing/${props.thingName}`,
        ],
      })
    )

    // Create and delete specific policy
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "iot:CreatePolicy",
          "iot:DeletePolicy",
          "iot:DeletePolicyVersion",
          "iot:ListPolicyVersions",
          "iot:ListTargetsForPolicy",
        ],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref(
            "AWS::Region"
          )}:${cdk.Fn.ref("AWS::AccountId")}:policy/${props.iotPolicyName}`,
        ],
      })
    )

    // Create SSM parameter
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["ssm:DeleteParameters", "ssm:PutParameter"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:ssm:${cdk.Fn.ref(
            "AWS::Region"
          )}:${cdk.Fn.ref("AWS::AccountId")}:parameter/${stackName}/${
            props.thingName
          }/private_key`,
          `arn:${cdk.Fn.ref("AWS::Partition")}:ssm:${cdk.Fn.ref(
            "AWS::Region"
          )}:${cdk.Fn.ref("AWS::AccountId")}:parameter/${stackName}/${
            props.thingName
          }/certificate_pem`,
        ],
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
          "iot:DescribeEndpoint",
          "iot:DetachPolicy",
          "iot:DetachThingPrincipal",
          "iot:ListAttachedPolicies",
          "iot:ListPrincipalThings",
          "iot:ListThingPrincipals",
          "iot:UpdateCertificate",
        ],
        resources: ["*"],
      })
    )

    // class public values
    this.certificatePemParameter = customResource.getAttString(
      "CertificatePemParameter"
    )
    this.privateKeySecretParameter = customResource.getAttString(
      "PrivateKeySecretParameter"
    )
    this.thingArn = customResource.getAttString("ThingArn")
    this.iotPolicyArn = customResource.getAttString("IotPolicyArn")
    this.certificateArn = customResource.getAttString("CertificateArn")
    this.dataAtsEndpointAddress = customResource.getAttString(
      "DataAtsEndpointAddress"
    )
    this.credentialProviderEndpointAddress = customResource.getAttString(
      "CredentialProviderEndpointAddress"
    )
  }

  // Separate static function to create or return singleton provider
  static getOrCreateProvider = (
    scope: Construct,
    resourceName: string
  ): cr.Provider => {
    const stack = cdk.Stack.of(scope)
    const uniqueId = resourceName
    const existing = stack.node.tryFindChild(uniqueId) as cr.Provider

    if (existing === undefined) {
      const createThingFn = new PythonFunction(stack, `${uniqueId}-Provider`, {
        entry: path.join(__dirname, "..", "assets"),
        index: "thing_cert_policy.py",
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(1),
        logRetention: logs.RetentionDays.ONE_MONTH,
      })
      // Role permissions are handled by the main constructor

      // Create the provider that invokes the Lambda function
      const createThingProvider = new cr.Provider(stack, uniqueId, {
        onEventHandler: createThingFn,
        logRetention: logs.RetentionDays.ONE_DAY,
      })
      return createThingProvider
    } else {
      // Second or additional call, use existing provider
      return existing
    }
  }
}
