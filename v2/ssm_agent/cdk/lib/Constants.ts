// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// IoT policy for SSM agent interaction
// NOTE - minimal policy from base accelerator provides Connect access
export const ssmAgentIoTPolicy = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Receive", "iot:Publish"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topic/<%= thingname %>/accelerator/ssm_agent/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Subscribe"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topicfilter/<%= thingname %>/accelerator/ssm_agent/*"
      ]
    }
  ]
}`
