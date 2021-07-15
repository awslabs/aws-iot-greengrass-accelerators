// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as lambda from "@aws-cdk/aws-lambda"

export const PYTHON_LAMBDA_RUNTIME: lambda.Runtime = lambda.Runtime.PYTHON_3_8

// Greengrass core minimal policy template
//
export const greengrassCoreMinimalIoTPolicy = {
  Version: "2012-10-17",
  Statement: [
    {
      Effect: "Allow",
      Action: ["iot:Connect"],
      Resource: "arn:aws:iot:region:account-id:client/{{ thing_name }}*"
    },
    {
      Effect: "Allow",
      Action: ["iot:Receive", "iot:Publish"],
      Resource: [
        "arn:aws:iot:region:account-id:topic/$aws/things/{{ thing_name }}*/greengrass/health/json",
        "arn:aws:iot:region:account-id:topic/$aws/things/{{ thing_name }}*/greengrassv2/health/json",
        "arn:aws:iot:region:account-id:topic/$aws/things/{{ thing_name }}*/jobs/*",
        "arn:aws:iot:region:account-id:topic/$aws/things/{{ thing_name }}*/shadow/*"
      ]
    },
    {
      Effect: "Allow",
      Action: ["iot:Subscribe"],
      Resource: [
        "arn:aws:iot:region:account-id:topicfilter/$aws/things/{{ thing_name }}*/jobs/*",
        "arn:aws:iot:region:account-id:topicfilter/$aws/things/{{ thing_name }}*/shadow/*"
      ]
    },
    {
      Effect: "Allow",
      Action: ["iot:GetThingShadow", "iot:UpdateThingShadow", "iot:DeleteThingShadow"],
      Resource: ["arn:aws:iot:region:account-id:thing/{{ thing_name }}*"]
    },
    {
      Effect: "Allow",
      Action: "iot:AssumeRoleWithCertificate",
      Resource: "arn:aws:iot:region:account-id:rolealias/token-exchange-role-alias-name"
    },
    {
      Effect: "Allow",
      Action: ["greengrass:GetComponentVersionArtifact", "greengrass:ResolveComponentCandidates", "greengrass:GetDeploymentConfiguration"],
      Resource: "*"
    }
  ]
}

export const greengrassMinimalRoleAliasPolicy = {
  Version: "2012-10-17",
  Statement: [
    {
      Effect: "Allow",
      Action: [
        "iot:DescribeCertificate",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive",
        "s3:GetBucketLocation"
      ],
      Resource: "*"
    }
  ]
}

// import json
// from jinja2 import Environment, BaseLoader

// x = '''{
//   "Version": "2012-10-17",
//   "Statement": [
//     {
//       "Effect": "Allow",
//       "Action": ["iot:Connect"],
//       "Resource": "arn:aws:iot:region:account-id:client/{{ thing_name }}*"
//     },
//     {
//       "Effect": "Allow",
//       "Action": ["iot:Receive", "iot:Publish"],
//       "Resource": [
//         "arn:aws:iot:region:account-id:topic/$aws/things/core-device-thing-name*/greengrass/health/json",
//         "arn:aws:iot:region:account-id:topic/$aws/things/core-device-thing-name*/greengrassv2/health/json",
//         "arn:aws:iot:region:account-id:topic/$aws/things/core-device-thing-name*/jobs/*",
//         "arn:aws:iot:region:account-id:topic/$aws/things/core-device-thing-name*/shadow/*"
//       ]
//     }
//   ]
// }'''
// rtemplate = Environment(loader=BaseLoader).from_string(x)
// rtemplate.render(thing_name="foo")
