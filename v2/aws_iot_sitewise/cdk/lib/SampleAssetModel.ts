// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Construct } from "constructs"
import * as cdk from "aws-cdk-lib"
import { aws_iotsitewise as sitewise } from "aws-cdk-lib"

export interface SampleAssetModelProps {}

export class SampleAssetModel extends Construct {
  public readonly ref: string

  private assetModel: sitewise.CfnAssetModel

  private composeLogicalId(idStub: string): string {
    return idStub
  }

  constructor(scope: Construct, id: string, props: SampleAssetModelProps) {
    super(scope, id)

    this.assetModel = new sitewise.CfnAssetModel(this, "SampleAssetModel", {
      assetModelName: "Sample Asset Model for AWS IoT SiteWise",
      assetModelDescription:
        "This is an asset model for the AWS IoT SiteWise Greengrass v2 Accelerator.",
      assetModelProperties: [
        {
            name: 'Type',
            dataType: 'STRING',
            logicalId: this.composeLogicalId('SampleAssetModelTypeAttribute'),
            type: {
                typeName: 'Attribute',
                attribute: { defaultValue: 'Test Device' }
            }
        },
        {
          name: "FreeMemory",
          dataType: "DOUBLE",
          logicalId: this.composeLogicalId(
            "SampleAssetModelFreeMemory"
          ),
          unit: "%",
          type: {
            typeName: "Measurement"
          }
        },
      ]
    })

    new cdk.CfnOutput(this, "SampleAssetModelId", {
      value: this.assetModel.ref,
      description: "LogicalID of sample asset model."
    })

    this.ref = this.assetModel.ref
  }
}
