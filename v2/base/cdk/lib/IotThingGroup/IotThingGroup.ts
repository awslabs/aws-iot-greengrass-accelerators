// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as path from "path"
import * as cdk from "@aws-cdk/core"
import * as logs from "@aws-cdk/aws-logs"
import * as iam from "@aws-cdk/aws-iam"
import * as cr from "@aws-cdk/custom-resources"
import * as lambda from "@aws-cdk/aws-lambda"

/**
 * @summary The properties for the IotThingGroup class.
 */
export interface IotThingGroupProps {
  /**
   * AWS IoT thing group name.
   *
   * @default - None
   */
  readonly thingGroupName: string
  /**
   * Optional name of the parent thing group.
   *
   * @default - None
   */
  readonly parentGroupName?: string
  /**
   * Optional description of the thing group.
   *
   * @default - None
   */
  readonly thingGroupDescription?: string
}
/**
 * This construct creates an AWS IoT thing group and provides methods to add or remove things from the group.
 *
 * @summary Create an AWS IoT thing group.
 */

/**
 * @summary The IotThingGroup class.
 */

export class IotThingGroup extends cdk.Construct {
  public readonly thingGroupName: string
  public readonly thingGroupArn: string
  public readonly thingGroupId: string

  private thingArnList: Array<string> = []

  private customResourceName = "IotThingGroupFunction"

  /**
   *
   * @summary Constructs a new instance of the IotRoleAlias class.
   * @param {cdk.App} scope - represents the scope for all the resources.
   * @param {string} id - this is a scope-unique id.
   * @param {IotThingGroupProps} props - user provided props for the construct.
   * @since 1.114.0
   */
  constructor(scope: cdk.Construct, id: string, props: IotThingGroupProps) {
    super(scope, id)

    const stackName = cdk.Stack.of(this).stackName

    // Validate and derive final values for resources
    const thingGroupDescription = props.thingGroupDescription || "CloudFormation generated group"

    const provider = IotThingGroup.getOrCreateProvider(this, this.customResourceName)
    const customResource = new cdk.CustomResource(this, this.customResourceName, {
      serviceToken: provider.serviceToken,
      properties: {
        // resources for lambda
        StackName: stackName,
        ThingGroupName: props.thingGroupName,
        ThingGroupDescription: thingGroupDescription,
        ThingArnList: this.thingArnList
      }
    })

    // Custom resource Lambda role permissions
    // Permissions for the resource specific calls
    provider.onEventHandler.role?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["iot:CreateThingGroup", "iot:DeleteThingGroup"],
        resources: [
          `arn:${cdk.Fn.ref("AWS::Partition")}:iot:${cdk.Fn.ref("AWS::Region")}:${cdk.Fn.ref("AWS::AccountId")}:thinggroup/${props.thingGroupName}`
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

    // class public values
    this.thingGroupName = customResource.getAttString("ThingGroupName")
    this.thingGroupArn = customResource.getAttString("ThingGroupArn")
    this.thingGroupId = customResource.getAttString("ThingGroupId")
  }
  // methods
  public addThing(thingArn: string): void {
    this.thingArnList.push(thingArn)
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
