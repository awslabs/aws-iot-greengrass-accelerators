// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import { Construct } from "constructs"
import * as cdk from "aws-cdk-lib"
import { aws_logs as logs } from "aws-cdk-lib"
import { aws_iam as iam } from "aws-cdk-lib"
import { aws_s3 as s3 } from "aws-cdk-lib"
import * as cr from "aws-cdk-lib/custom-resources"
import * as lambda from "aws-cdk-lib/aws-lambda"
import * as assets from "aws-cdk-lib/aws-s3-assets"
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha"
import exp = require("constants")

/**
 * @summary The properties for the GreengrassComponent class.
 */
export interface GreengrassV2ComponentProps {
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
   * S3 Bucket to upload component artifacts.
   *
   * @default - None
   */
  readonly bucket: s3.IBucket
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
   * Full path to the base recipe file. It will be processed to replace `COMPONENT_BUCKET` with
   * actual value.
   * @default - None
   */
  readonly sourceRecipeFile: string
  /**
   * Optional S3 object key to be for the compressed artifacts. The recipe variable ARTIFACT_KEY_NAME
   * found in the recipe file will be replaced with the provided value, leading `/` removed if provided.
   * Otherwise the value in the recipe file URI must match what is provided.
   *
   * A value of `path1/path2/component-version.zip` would be represented as:
   * `"URI": "s3:/bucket_name/path1/path2/component-version.zip"`
   *
   * @default - ${componentName}-${componentVersion}.zip
   */
  readonly targetArtifactKeyName?: string
}
/**
 * This construct creates an AWS IoT Greengrass component, uploads the artifacts to S3, and publishes
 * the component.
 * @summary The GreengrassComponent class.
 */

export class GreengrassV2Component extends Construct {
  public readonly componentName: string
  public readonly componentVersion: string
  public readonly componentArn: string
  private customResourceName = "GreengrassV2ComponentFunction"
  /**
   *
   * @summary Constructs a new instance of the IotRoleAlias class.
   * @param {cdk.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {GreengrassV2ComponentProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: Construct, id: string, props: GreengrassV2ComponentProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName

    // Validate and derive final values for resources
    // Set prefix path to nothing by default, otherwise path with trailing /
    var componentPrefixPath = props.artifactZipPrefix || ""
    if (componentPrefixPath !== "") {
      componentPrefixPath += componentPrefixPath.endsWith("/") ? "" : "/"
    }
    const targetArtifactKeyName =
      props.targetArtifactKeyName ||
      `${this.componentName}-${this.componentVersion}.zip`
    targetArtifactKeyName.replace(/^\//, "")

    // create zip file of artifacts in CDK source bucket as has values
    // will replace as targetArtifactKeyName is user's component bucket
    const componentZipAsset = new assets.Asset(this, "ComponentZipAsset", {
      path: props.sourceArtifactPath,
    })
    const recipeFileAsset = new assets.Asset(this, "RecipeFileAsset", {
      path: props.sourceRecipeFile,
    })

    const provider = GreengrassV2Component.getOrCreateProvider(
      this,
      this.customResourceName
    )
    const customResource = new cdk.CustomResource(
      this,
      this.customResourceName,
      {
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
          TargetArtifactKeyName: targetArtifactKeyName,
        },
      }
    )

    // Custom resource Lambda role permissions
    // Permissions for the resource specific calls
    // Access to target bucket
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject",
          "s3:GetBucketLocation",
        ],
        resources: [
          `arn:aws:s3:::${props.bucket.bucketName}/*`,
          `arn:aws:s3:::${props.bucket.bucketName}/*`,
        ],
      })
    )
    // Read from staging bucket
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["s3:GetObject"],
        resources: [
          `arn:aws:s3:::${componentZipAsset.s3BucketName}/${componentZipAsset.s3ObjectKey}`,
          `arn:aws:s3:::${recipeFileAsset.s3BucketName}/${recipeFileAsset.s3ObjectKey}`,
        ],
      })
    )
    // Create component
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["greengrass:CreateComponentVersion"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:greengrass:${cdk.Fn.ref(
            "AWS::Region"
          )}:${cdk.Fn.ref("AWS::AccountId")}:components:${props.componentName}`,
        ],
      })
    )
    // Describe component
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["greengrass:DeleteComponent", "greengrass:DescribeComponent"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:greengrass:${cdk.Fn.ref(
            "AWS::Region"
          )}:${cdk.Fn.ref("AWS::AccountId")}:components:${
            props.componentName
          }:versions:${props.componentVersion}`,
        ],
      })
    )

    // Permissions needed for all resources
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:AddThingToThingGroup"],
        resources: ["*"],
      })
    )
    // class public values
    this.componentName = props.componentName
    this.componentVersion = props.componentVersion
    this.componentArn = customResource.getAttString("ComponentArn")
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
        entry: path.join(__dirname, "../", "assets"),
        index: "create_component_version.py",
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: cdk.Duration.minutes(10),
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
