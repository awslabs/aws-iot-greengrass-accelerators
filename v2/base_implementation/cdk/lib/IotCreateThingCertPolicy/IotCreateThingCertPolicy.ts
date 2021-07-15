// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"
import { PythonFunction } from "@aws-cdk/aws-lambda-python"

/**
 * @summary The properties for the IotCreateThingCertPolicy class.
 */
export interface IotCreateThingCertPolicyProps {
  /**
   * Name of CloudFormation stack used as part of thing name
   */
  stackName?: string
  /** Name of AWS IoT thing to create */
  thingName: string
  /** If defined, AWS IoT generated certificate is created and attached to the Thing and Policy. Private key available through returned Parameter store Arn  */
  createCertificate?: boolean
  /** The AWS IoT policy to be created and attached to the certificate. If defined, `createCertificate` must also be included.
   *  The policy supports Jinja2 fields to replace mappings such as `{{ thingName }}` with the provided values in the `policyParameterMapping` object.
   */
  iotPolicy?: object
  /** A list of parameters in the iotPolicy to be replaced with values (Jinja2) */
  policyParameterMapping?: object
}

export class IotCreateThingCertPolicy extends cdk.Construct {
  public readonly thingArn: string
  public readonly certificateArn: string
  public readonly certificatePem: string
  public readonly privateKeySecretArn: string

  constructor(scope: cdk.Construct, id: string, props: IotCreateThingCertPolicyProps) {
    super(scope, id)

    // Validate properties
    if (props.iotPolicy && !props.createCertificate) {
      throw new Error("createCertificate must be set when providing an AWS IoT policy")
    }
    const createCertificate = props.createCertificate || false
    const iotPolicy = props.iotPolicy || {}

    const createThingFn = new PythonFunction(this, "MyHandler", {
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: cdk.Duration.minutes(1),
      index: "create_thing.py",
      handler: "handler",
      entry: path.join(__dirname, "assets")
    })
    // Add permissions for AWS calls within the Lambda function
    if (createThingFn.role) {
      createThingFn.role.addToPrincipalPolicy(new iam.PolicyStatement({ actions: ["iot:*"], resources: ["*"] }))
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
        ThingName: props.thingName,
        CreateCertificate: createCertificate,
        IotPolicy: iotPolicy
      }
    })

    // Set resource return values from function
    this.certificatePem = customResource.getAttString("CertificatePem")
    this.privateKeySecretArn = customResource.getAttString("PrivateKeySecretArn")
    this.thingArn = customResource.getAttString("ThingArn")
    this.certificateArn = customResource.getAttString("CertificateArn")
  }
}
