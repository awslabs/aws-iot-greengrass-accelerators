// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// IoT policy for source event interaction
// NOTE - minimal policy from base accelerator provides Connect access
export const sourceEventIoTPolicy = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Receive", "iot:Publish"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topic/<%= thingname %>/accelerator/source_event/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Subscribe"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topicfilter/<%= thingname %>/accelerator/source_event/*"
      ]
    }
  ]
}`
