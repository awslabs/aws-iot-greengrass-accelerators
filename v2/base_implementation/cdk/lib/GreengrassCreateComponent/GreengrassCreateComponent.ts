// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as s3 from "@aws-cdk/aws-s3"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"

/**
 * @summary The properties for the GreengrassComponent class.
 */
export interface GreengrassCreateComponentProps {
  /**
   * AWS IoT Greengrass component name.
   *
   * @default - None
   */
  readonly componentName: string
  /**
   * AWS IoT Greengrass component version.
   *
   * @default - None
   */
  readonly componentVersion: string
  /**
   * S3 Bucket  to upload component artifacts
   *
   * @default - None
   */
  readonly bucket: s3.Bucket
  /**
   * Directory path to the artifacts. Should be `../somewhere/artifacts`, and then componentName
   * and componentVersion will be used to complete.
   *
   * @default - None
   */
  readonly artifactPath: string
  /**
   * Full path to the base recipe file. It will be processed to replace ${COMPONENT_BUCKET} with
   * actual value.
   * @default - None
   */
  readonly recipeFile: string
}
/**
 * This construct creates an AWS IoT Greengrass component, uploads the artifacts to S3, and publishes
 * the component.
 *
 * @summary Create an AWS IoT Greengrass component.
 */

/**
 * @summary The GreengrassComponent class.
 */

export class GreengrassCreateComponent extends cdk.Construct {
  private customResourceName = "GreengrassCreateComponentFunction"

  /**
   *
   * @summary Constructs a new instance of the IotRoleAlias class.
   * @param {cdk.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {GreengrassComponentProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: cdk.Construct, id: string, props: GreengrassCreateComponentProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName

    // Validate and derive final values for resources

    const provider = GreengrassCreateComponent.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        // resources for lambda
        StackName: stackName
      }
    })

    // Custom resource Lambda role permissions
    // Permissions for the resource specific calls
    // Permissions needed for all resources
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:AddThingToThingGroup"],
        resources: ["*"]
      })
    )
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
        handler: "thing_group.handler",
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
