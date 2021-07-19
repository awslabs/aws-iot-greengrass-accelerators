# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
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


def create_iot_role_alias(role_alias_name, iam_role_arn):
    c_iot = get_aws_client("iot")

    # Create IoT Role alias with IAM role
    try:
        c_iot.create_role_alias(
            roleAlias=role_alias_name,
            roleArn=iam_role_arn,
        )
    except ClientError as e:
        logger.warning(
            f"Error calling iot.create_role_alias() for role alias {role_alias_name}, error: {e}"
        )


def delete_iot_role_alias(role_alias_name):
    c_iot = get_aws_client("iot")

    # Delete the IoT role alias
    try:
        c_iot.delete_role_alias(roleAlias=role_alias_name)
    except ClientError as e:
        logger.warning(
            f"Error calling iot.delete_role_alias() for role alias {role_alias_name}, error: {e}"
        )


def handler(event, context):
    logger.info("Received event: %s", event)
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
            response = create_iot_role_alias(
                role_alias_name=props["IotRoleAliasName"],
                iam_role_arn=props["IamRoleArn"],
            )
            response_data = {}
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            delete_iot_role_alias(
                role_alias_name=props["IotRoleAliasName"],
            )
            logger.info(f'Role alias {props["IotRoleAliasName"]} successfully deleted')
            response_data = {}
        else:
            logger.error("Should not get here in normal cases - could be REPLACE")
        # Resource id set to unique IAM role name
        output = {
            "PhysicalResourceId": props["IotRoleAliasName"],
            "Data": response_data,
        }
        logger.info("Output from Lambda: %s", json.dumps(output, indent=2))
        return output
    except Exception as e:
        logger.exception(e)