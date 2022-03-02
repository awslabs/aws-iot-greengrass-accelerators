// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import "source-map-support/register"
import * as cdk from "aws-cdk-lib"
import { BaseImplementationStack } from "../lib/BaseImplementationStack"

const app = new cdk.App()
const name = process.env.STACK_NAME || "gg-accel-base"

new BaseImplementationStack(app, name, {
  env: {
    account: process.env.CDK_DEPLOY_ACCOUNT || process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEPLOY_REGION || process.env.CDK_DEFAULT_REGION
  },
  stackName: name,
  description: "Greengrass Accelerator v2 - Base Implementation for development"
})
