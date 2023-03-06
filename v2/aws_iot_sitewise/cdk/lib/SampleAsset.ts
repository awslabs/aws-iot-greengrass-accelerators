// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { Construct } from "constructs"
import * as cdk from "aws-cdk-lib"
import { aws_iotsitewise as sitewise } from "aws-cdk-lib"

export interface SampleAssetProps {
  condition: cdk.CfnCondition
  assetName: string
  assetModelId: string
  propertyAlias: string
}

export class SampleAsset extends Construct {
  public readonly ref: string

  private asset: sitewise.CfnAsset

  constructor(scope: Construct, id: string, props: SampleAssetProps) {
    super(scope, id)

    this.asset = new sitewise.CfnAsset(this, "SampleAsset", {
      assetModelId: props.assetModelId,
      assetName: props.assetName,
      assetProperties: [
        {
          logicalId: "SampleAssetModelFanSpeed",
          alias: props.propertyAlias
        }
      ]
    })

    this.asset.cfnOptions.condition = props.condition
    this.ref = this.asset.ref
  }
}

