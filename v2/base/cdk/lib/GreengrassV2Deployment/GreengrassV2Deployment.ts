// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "aws-cdk-lib"
import {aws_logs as logs} from "aws-cdk-lib"
import {aws_iam as iam} from "aws-cdk-lib"
import * as cr from "aws-cdk-lib/custom-resources"
import * as lambda from "aws-cdk-lib/aws-lambda"
import { Construct } from 'constructs'

/**
 * @summary A component definition
 */
export interface Component {
  [componentName: string]: {
    componentVersion: string
    configurationUpdate?: {
      merge?: string
      reset?: string
    }
  }
}

/**
 * @summary The properties for the GreengrassCreateDeployment class.
 */
export interface GreengrassV2DeploymentProps {
  /**
   * Target Arn (thing or thingGroup) for deployment
   *
   * @default - None
   */
  readonly targetArn: string
  /**
   * Name to describe the deployment.
   *
   * @default - None
   */
  readonly deploymentName: string
  /**
   * List of components to deploy along with optional merge and reset values
   * TODO - define interface with component config
   *
   * @default - None
   */
  readonly component: Component
  /**
   * Optional IoT job configuration
   * TODO - define interface and logic
   *
   * @default - None
   */
  readonly iotJobConfiguration?: object
  /**
   * Optional deployment polices for failure handling, component update, and
   * validity of the policy
   * TODO - define interface and logic
   *
   * @default - None
   */
  readonly deploymentPolicies?: object
  /**
   * Optional tags to add to deployment
   * TODO - logic and method to add tags
   *
   * @default - None
   */
  readonly tags?: cdk.Tags
}

/**
 * This construct creates a Greengrass v2 deployment targeted to an individual thing
 * or thingGroup.
 *
 * @summary Creates an AWS IoT role alias and referenced IAM role with provided IAM policy.
 */

/**
 * @summary The IotRoleAlias class.
 */

export class GreengrassV2Deployment extends Construct {
  public readonly deploymentId: string
  public readonly iotJobId: string
  public readonly iotJobArn: string

  private customResourceName = "GreengrassV2DeploymentFunction"
  private componentList: Component = {}

  /**
   *
   * @summary Constructs a new instance of the IotRoleAlias class.
   * @param {cdk.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {GreengrassV2DeploymentProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: Construct, id: string, props: GreengrassV2DeploymentProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName
    this.componentList = props.component

    // Validate and derive final values for resources

    const provider = GreengrassV2Deployment.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        StackName: stackName,
        TargetArn: props.targetArn,
        DeploymentName: props.deploymentName,
        // object of objects { "compA": {..}, "compB": {...} }
        Components: this.componentList,
        IotJobExecution: props.iotJobConfiguration || {},
        DeploymentPolicies: props.deploymentPolicies || {},
        Tags: props.tags || {}
      }
    })

    // Custom resource Lambda role permissions
    // Permissions for Creating or cancelling deployment - requires expanded permissions to interact with
    // things and jobs
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "greengrass:CancelDeployment",
          "greengrass:CreateDeployment",
          "iot:CancelJob",
          "iot:CreateJob",
          "iot:DeleteThingShadow",
          "iot:DescribeJob",
          "iot:DescribeThing",
          "iot:DescribeThingGroup",
          "iot:GetThingShadow",
          "iot:UpdateJob",
          "iot:UpdateThingShadow"
        ],
        resources: ["*"]
      })
    )

    // class public values
    // this.iamRoleArn = iamRole.roleArn
    this.deploymentId = customResource.getAttString("DeploymentId")
    this.iotJobId = customResource.getAttString("IotJobId")
    this.iotJobArn = customResource.getAttString("IotJobArn")
  }

  public addComponent = (component: Component) => {
    Object.keys(component).forEach((key) => {
      if (key in this.componentList) {
        console.error("Duplicate components not allowed. Component ", key, " already part of deployment.")
        process.exitCode = 1
      } else {
        this.componentList[key] = component[key]
      }
    })
  }

  // Separate static function to create or return singleton provider
  static getOrCreateProvider = (scope: Construct, resourceName: string): cr.Provider => {
    const stack = cdk.Stack.of(scope)
    const uniqueId = resourceName
    const existing = stack.node.tryFindChild(uniqueId) as cr.Provider

    if (existing === undefined) {
      const createThingFn = new lambda.Function(stack, `${uniqueId}-Provider`, {
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(5),
        handler: "create_deployment.handler",
        code: lambda.Code.fromAsset(path.join(__dirname, "assets")),
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
