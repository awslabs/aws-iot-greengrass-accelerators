// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import "source-map-support/register"
import * as cdk from "@aws-cdk/core"
import { SourceEventStack } from "../lib/SourceEventStack"

const app = new cdk.App()
const name = process.env.STACK_NAME || "gg-accel-source-event"

new SourceEventStack(app, name, {
  env: {
    account: process.env.CDK_DEPLOY_ACCOUNT || process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEPLOY_REGION || process.env.CDK_DEFAULT_REGION
  },
  stackName: name,
  description: "Greengrass Accelerator v2 - Source Event Component"
})
