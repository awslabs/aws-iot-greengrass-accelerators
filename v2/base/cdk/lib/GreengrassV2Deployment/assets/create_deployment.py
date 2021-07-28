# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import logging as logger
import boto3
import botocore
from botocore.exceptions import ClientError


logger.getLogger().setLevel(logger.INFO)


def get_aws_client(name):
    return boto3.client(
        name,
        config=botocore.config.Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def create_deployment(target_arn: str, deployment_name: str, components: object):
    c_greengrassv2 = get_aws_client("greengrassv2")
    result = {}

    # Create deployment
    try:
        response = c_greengrassv2.create_deployment(
            targetArn=target_arn, deploymentName=deployment_name, components=components
        )
        result["deploymentId"] = response["deploymentId"]
        result["iotJobId"] = response["iotJobId"]
        result["iotJobArn"] = response["iotJobArn"]
    except ClientError as e:
        raise ValueError(
            f"Error calling create_deployment for target {target_arn}, error: {e}"
        )
    except Exception as e:
        raise ValueError(
            f"Could not create deployment, return FAILED to calling function, {e}"
        )
    return result


def cancel_deployment(deployment_id: str):
    c_greengrassv2 = get_aws_client("greengrassv2")

    # Cancel the Greengrass deployment
    try:
        response = c_greengrassv2.cancel_deployment(deploymentId=deployment_id)
        logger.info(
            f"Successfully canceled Greengrass deployment {deployment_id}, response was: {response}"
        )
    except ClientError as e:
        logger.warning(
            f"Error calling greengrassv2.cancel_deployment() for deployment id {deployment_id}, error: {e}"
        )


def handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))
    logger.info("Environment: %s", dict(os.environ))
    props = event["ResourceProperties"]
    try:
        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            logger.info("Request CREATE")
            try:
                response = create_deployment(
                    target_arn=props["TargetArn"],
                    deployment_name=props["DeploymentName"],
                    components=props["Components"],
                    # iot_job_execution=props["IotJobExecution"],
                    # deployment_policies=props["DeploymentPolicies"],
                    # tags=props["Tags"]
                )
                # Populate Pascal
                response_data = {
                    "DeploymentId": response["deploymentId"],
                    "IotJobId": response["iotJobId"],
                    "IotJobArn": response["iotJobArn"],
                }
                physical_resource_id = response["deploymentId"]
            except ValueError as e:
                logger.error(e)
                sys.exit(1)
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            cancel_deployment(deployment_id=event["PhysicalResourceId"])
            logger.info(
                f'DELETE Request: Greengrass deployment {event["PhysicalResourceId"]} successfully cancelled'
            )
            response_data = {}
            physical_resource_id = event["PhysicalResourceId"]
        else:
            logger.error("Should not get here in normal cases - could be REPLACE")
        # Resource id set to unique IAM role name
        output = {
            "PhysicalResourceId": physical_resource_id,
            "Data": response_data,
        }
        logger.info("Output from Lambda: %s", json.dumps(output, indent=2))
        return output
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
