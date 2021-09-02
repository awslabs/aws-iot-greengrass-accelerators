// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// In its current form, this code is not fit for production workloads.

// IoT policy for source event interaction
// NOTE - minimal policy from base accelerator provides Connect access
export const etlSimpleIoTPolicy = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Publish"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topic/<%= thingname %>/etl_simple/*"
      ]
    }
  ]
}`
