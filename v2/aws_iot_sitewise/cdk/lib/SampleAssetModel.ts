// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Construct } from "constructs"
import * as cdk from "aws-cdk-lib"
import { aws_iotsitewise as sitewise } from "aws-cdk-lib"

export interface SampleAssetModelProps {
  condition: cdk.CfnCondition
}

export class SampleAssetModel extends Construct {
  public readonly ref: string

  private assetModel: sitewise.CfnAssetModel

  constructor(scope: Construct, id: string, props: SampleAssetModelProps) {
    super(scope, id)

    this.assetModel = new sitewise.CfnAssetModel(this, "SampleAssetModel", {
      assetModelName: "Sample Asset Model for AWS IoT SiteWise",
      assetModelDescription:
        "This is an asset model for the AWS IoT SiteWise Greengrass v2 Accelerator.",
      assetModelProperties: [
        {
          name: "Type",
          dataType: "STRING",
          logicalId: "SampleAssetModelType",
          type: {
            typeName: "Attribute",
            attribute: { defaultValue: "Test Device" }
          }
        },
        {
          name: "FanSpeed",
          dataType: "DOUBLE",
          logicalId: "SampleAssetModelFanSpeed",
          unit: "rpm",
          type: {
            typeName: "Measurement"
          }
        }
      ]
    })

    this.assetModel.cfnOptions.condition = props.condition
    this.ref = this.assetModel.ref
  }
}
