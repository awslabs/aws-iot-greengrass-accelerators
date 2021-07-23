// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as s3 from "@aws-cdk/aws-s3"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"
import * as assets from "@aws-cdk/aws-s3-assets"
import { PythonFunction } from "@aws-cdk/aws-lambda-python"

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
   * and componentVersion will be used to complete. Contents will be compressed in ZIP format.
   *
   * @default - None
   */
  readonly sourceArtifactPath: string
  /**
   * Optional - Prefix and path for artifact zip file.
   *
   * @default - None
   */
  readonly artifactZipPrefix?: string
  /**
   * Full path to the base recipe file. It will be processed to replace ${COMPONENT_BUCKET} with
   * actual value.
   * @default - None
   */
  readonly sourceRecipeFile: string
  /**
   * Optional S3 object key to be for the compressed artifacts. The recipe variable ${ARTIFACT_KEY_NAME}
   * found in the recipe file will be replaced with the provided value, leading `/` removed if provided.
   * Otherwise the value in the recipe file URI must match what is provided.
   *
   * A value of `path1/path2/component-version.zip` would be represented as:
   * `"URI"L "s3:/bucket_name/path1/path2/component-version.zip"`
   *
   * @default - ${componentName}-${componentVersion}.zip
   */
  readonly targetArtifactKeyName?: string
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
    const componentPrefixPath = props.artifactZipPrefix || ""
    const targetArtifactKeyName = props.targetArtifactKeyName || ""
    targetArtifactKeyName.replace(/^\//, "")

    // create zip file of artifacts (component-version.zip)
    const componentZipAsset = new assets.Asset(this, "ComponentZipAsset", {
      path: props.sourceArtifactPath
    })
    const recipeFileAsset = new assets.Asset(this, "RecipeFileAsset", {
      path: props.sourceRecipeFile
    })

    const provider = GreengrassCreateComponent.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        // resources for lambda
        StackName: stackName,
        AssetBucket: componentZipAsset.s3BucketName,
        ComponentZipAsset: componentZipAsset.s3ObjectKey,
        ComponentPrefixPath: componentPrefixPath,
        RecipeFileAsset: recipeFileAsset.s3ObjectKey,
        ComponentName: props.componentName,
        ComponentVersion: props.componentVersion,
        TargetBucket: props.bucket.bucketName,
        TargetArtifactKeyName: targetArtifactKeyName
      }
    })

    // Custom resource Lambda role permissions
    // Permissions for the resource specific calls
    // Access to target bucket
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["s3:PutObject", "s3:GetObject", "s3:ListBucket", "s3:DeleteObject", "s3:GetBucketLocation"],
        resources: [`arn:aws:s3:::${props.bucket.bucketName}/*`, `arn:aws:s3:::${props.bucket.bucketName}/*`]
      })
    )
    // Read from staging bucket
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["s3:GetObject"],
        resources: [
          `arn:aws:s3:::${componentZipAsset.s3BucketName}/${componentZipAsset.s3ObjectKey}`,
          `arn:aws:s3:::${recipeFileAsset.s3BucketName}/${recipeFileAsset.s3ObjectKey}`
        ]
      })
    )
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
      const createThingFn = new PythonFunction(stack, `${uniqueId}-Provider`, {
        entry: path.join(__dirname, "assets"),
        index: "create_component_version.py",
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(10),
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
