// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as lambda from "@aws-cdk/aws-lambda"

export const PYTHON_LAMBDA_RUNTIME: lambda.Runtime = lambda.Runtime.PYTHON_3_8

// Greengrass core minimal policy template
// NOTE: Additional permissions may be needed for components
export const greengrassCoreMinimalIoTPolicy = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Connect"],
      "Resource": "arn:aws:iot:<%= region %>:<%= account %>:client/<%= completePolicyName %>*"
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Receive", "iot:Publish"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topic/$aws/things/<%= completePolicyName %>*/greengrass/health/json",
        "arn:aws:iot:<%= region %>:<%= account %>:topic/$aws/things/<%= completePolicyName %>*/greengrassv2/health/json",
        "arn:aws:iot:<%= region %>:<%= account %>:topic/$aws/things/<%= completePolicyName %>*/jobs/*",
        "arn:aws:iot:<%= region %>:<%= account %>:topic/$aws/things/<%= completePolicyName %>*/shadow/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Subscribe"],
      "Resource": [
        "arn:aws:iot:<%= region %>:<%= account %>:topicfilter/$aws/things/<%= completePolicyName %>*/jobs/*",
        "arn:aws:iot:<%= region %>:<%= account %>:topicfilter/$aws/things/<%= completePolicyName %>*/shadow/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:GetThingShadow", "iot:UpdateThingShadow", "iot:DeleteThingShadow"],
      "Resource": ["arn:aws:iot:<%= region %>:<%= account %>:thing/<%= completePolicyName %>*"]
    },
    {
      "Effect": "Allow",
      "Action": "iot:AssumeRoleWithCertificate",
      "Resource": "arn:aws:iot:<%= region %>:<%= account %>:rolealias/<%= rolealiasname %>"
    },
    {
      "Effect": "Allow",
      "Action": ["greengrass:GetComponentVersionArtifact", "greengrass:ResolveComponentCandidates", "greengrass:GetDeploymentConfiguration"],
      "Resource": "*"
    }
  ]
}`
