// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import "source-map-support/register"
import * as cdk from "aws-cdk-lib"
import { SiteWiseStack } from "../lib/SiteWiseStack"

const app = new cdk.App()
const name = process.env.STACK_NAME || "gg-accel-stitewise"

new SiteWiseStack(app, name, {
  env: {
    account: process.env.CDK_DEPLOY_ACCOUNT || process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEPLOY_REGION || process.env.CDK_DEFAULT_REGION
  },
  stackName: name,
  description: "Greengrass Accelerator v2 - SiteWise Component"
})
