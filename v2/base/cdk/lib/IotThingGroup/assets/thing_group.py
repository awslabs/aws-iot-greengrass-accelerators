# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import re
import logging as logger
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

import time

logger.getLogger().setLevel(logger.INFO)


def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def validate_thing_arn(arn: str):
    """Validate the thing Arn

    :param arn: Thing Arn to validate
    :type arn: str
    """
    p = re.compile("^arn:aws:iot:.+:[0-9]+:thing/.+")
    if p.match(arn):
        return True
    else:
        return False


def create_resources(
    group_name: str,
    group_description: str,
    thing_list: list,
):
    """Create AWS IoT thing group, and add any listed things to it"""
    c_iot = get_aws_client("iot")
    result = {}

    # Validate the things to add to verify they are IoT thing Arns
    for thing_arn in thing_list:
        if not validate_thing_arn(thing_arn):
            logger.error(f"Invalid thing arn {thing_arn}, exiting")
            sys.exit(1)

    # create thing group
    try:
        response = c_iot.create_thing_group(
            thingGroupName=group_name,
            thingGroupProperties={"thingGroupDescription": group_description},
        )
        result["ThingGroupName"] = response["thingGroupName"]
        result["ThingGroupArn"] = response["thingGroupArn"]
        result["ThingGroupId"] = response["thingGroupId"]
    except ClientError as e:
        logger.error(f"Unable to create thing group {group_name}, {e}")
        sys.exit(1)

    # Add things to group
    try:
        for thing in thing_list:
            c_iot.add_thing_to_thing_group(thingGroupName=group_name, thingArn=thing)
    except ClientError as e:
        logger.error(
            f"Error adding things {thing_list} to thing group {group_name}, {e}"
        )
        sys.exit(1)

    return result


def delete_resources(group_name: str):
    """Delete thing group after removing all things or sub-groups"""

    c_iot = get_aws_client("iot")

    # delete thing group - No need to remove things first
    try:
        c_iot.delete_thing_group(thingGroupName=group_name)
    except ClientError as e:
        logger.error(f"Unable to delete thing group {group_name}, {e}")


def handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))
    logger.info("Environment: %s", dict(os.environ))
    props = event["ResourceProperties"]
    physical_resource_id = ""
    try:
        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            logger.info("Request CREATE")
            resp = create_resources(
                group_name=props["ThingGroupName"],
                group_description=props["ThingGroupDescription"],
                thing_list=props["ThingArnList"],
            )

            # set response data (PascalCase key)
            response_data = {
                "ThingGroupName": resp["ThingGroupName"],
                "ThingGroupArn": resp["ThingGroupArn"],
                "ThingGroupId": resp["ThingGroupId"],
            }
            physical_resource_id = response_data["ThingGroupName"]
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            resp = delete_resources(
                group_name=props["ThingGroupName"],
            )
            response_data = {}
            physical_resource_id = event["PhysicalResourceId"]
        else:
            logger.info("Should not get here in normal cases - could be REPLACE")

        output = {"PhysicalResourceId": physical_resource_id, "Data": response_data}
        logger.info("Output from Lambda: %s", json.dumps(output, indent=2))
        return output
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
