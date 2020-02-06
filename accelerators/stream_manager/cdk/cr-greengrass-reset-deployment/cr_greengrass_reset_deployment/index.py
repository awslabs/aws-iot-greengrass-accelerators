"""
Custom resource function to reset a Greengrass deployment prior to deleting Greengrass Group
"""

import json
import os
import logging
import time
import boto3
import cfnresponse
from botocore.exceptions import ClientError

__copyright__ = (
    "Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved."
)
__license__ = "MIT-0"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def find_group_id(groupName):
    """Return Greengrass group id"""
    result = ""
    greengrass_client = boto3.client("greengrass")

    response = greengrass_client.list_groups()
    for group in response["Groups"]:
        if groupName == group["Name"]:
            result = group["Id"]
            break
    return result


def main(event, context):

    greengrass_client = boto3.client("greengrass")

    # NOTE: All ResourceProperties passed will uppercase the first letter
    #       of the property and leave the rest of the case intact.

    physical_id = event["ResourceProperties"]["PhysicalId"]
    cfn_response = cfnresponse.SUCCESS

    try:
        logger.info("Input event: %s", event)

        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            logger.info("Create called, no actions being taken")
            # Nothing is done during Create
            response_data = {}
        elif event["RequestType"] == "Update":
            # Nothing is done during Update
            logger.info("Update called, no actions being taken")
            response_data = {}
        else:
            # Delete request
            # Reset deployment for Greengrass
            logger.info(
                "Delete called, will attempt to reset Deployment on %s"
                % event["ResourceProperties"]["GreengrassGroup"]
            )
            group_id = find_group_id(event["ResourceProperties"]["GreengrassGroup"])
            logger.info("Group id to delete: %s" % group_id)
            if group_id:
                greengrass_client.reset_deployments(Force=True, GroupId=group_id)
                result = cfnresponse.SUCCESS
                logger.info("Forced reset of Greengrass deployment")
            else:
                logger.error(
                    "No group Id %s found, reset not required"
                    % event["ResourceProperties"]["GreengrassGroup"]
                )
            response_data = {}
        cfnresponse.send(event, context, cfn_response, response_data, physical_id)

    except Exception as e:
        logger.exception(e)
        # cfnresponse error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
