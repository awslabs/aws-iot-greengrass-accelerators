// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// IoT policy for source event interaction
// NOTE - minimal policy from base accelerator provides Connect access
export const siteWiseIoTPolicy = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Connect"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Receive", "iot:Publish"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Subscribe"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["iot:GetThingShadow", "iot:UpdateThingShadow", "iot:DeleteThingShadow"],
      "Resource": ["arn:aws:iot:<%= region %>:<%= account %>:thing/<%= thingname %>*"]
    }
  ]
}`
