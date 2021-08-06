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

greengrass_client = boto3.client("greengrass")


def create_deployment(group_id):
    """Initiate a reset for the given Group Id"""
    logger.info("Group id to deploy: %s" % group_id)
    group_version = greengrass_client.list_group_versions(GroupId=group_id)["Versions"][
        0
    ]["Version"]
    greengrass_client.create_deployment(
        DeploymentType="NewDeployment", GroupId=group_id, GroupVersionId=group_version,
    )


def reset_deployment(group_id):
    """Force reset the deployment on the given Group Id"""
    greengrass_client.reset_deployments(Force=True, GroupId=group_id)


def main(event, context):
    """Invoked by CloudFormation, event contains the passed parameters
    
    NOTE: All ResourceProperties passed will uppercase the first letter
          of the property and leave the rest of the case intact.
    """
    physical_id = event["ResourceProperties"]["PhysicalId"]
    group_name = event["ResourceProperties"]["GreengrassGroupName"]
    group_id = event["ResourceProperties"]["GreengrassGroupId"]
    cfn_response = cfnresponse.SUCCESS
    response_data = {}

    try:
        # Log event for troubleshooting
        logger.info("Input event: %s", event)
        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            # Create an initial deployment so when Docker starts, Greengrass will pull down
            logger.info("Creating the initial deployment for Greengrass group: %s" % group_name)
            create_deployment(group_id)
            logger.info("Initiated the first deployment to the group: %s" % group_name)
        elif event["RequestType"] == "Update":
            # An update requires that the Group be not be deployed if making changes to any Greegrass
            # resources. So perform a reset_deployment and then deploy again
            logger.info(
                "Update called, forcing reset of deployment and then creating new deployment"
            )
            # Reset deployment
            logger.info("Group id to force deployment reset: %s" % group_id)
            reset_deployment(group_id)
            # Deploy again for changes to be pushed to Core
            logger.info("Group id to deploy: %s" % group_id)
            create_deployment(group_id)
        else:
            # Delete request
            # Reset deployment for Greengrass
            logger.info(
                "Delete called, will attempt to reset Deployment on group: %s"
                % group_name
            )
            logger.info("Group id to delete: %s" % group_id)
            reset_deployment(group_id)

        cfnresponse.send(event, context, cfn_response, response_data, physical_id)

    except Exception as e:
        logger.exception(e)
        # cfnresponse error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
