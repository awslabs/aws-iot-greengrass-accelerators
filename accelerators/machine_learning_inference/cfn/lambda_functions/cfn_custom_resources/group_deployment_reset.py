import os
import sys
import json
import logging
import cfnresponse
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

c = boto3.client("greengrass")

def handler(event, context):
    responseData = {}
    try:
        logger.info("Received event: {}".format(json.dumps(event)))
        result = cfnresponse.FAILED
        group_id = event["ResourceProperties"]["GroupId"]
        # role_name = event["ResourceProperties"]["RoleName"]
        if event["RequestType"] == "Create":
            result = cfnresponse.SUCCESS
        elif event["RequestType"] == "Update":
            # No action required on Update
            result = cfnresponse.SUCCESS
        elif event["RequestType"] == "Delete":
            logger.info("Group id to delete: %s" % group_id)
            if group_id:
                c.reset_deployments(Force=True, GroupId=group_id)
                result = cfnresponse.SUCCESS
                logger.info("Forced reset of Greengrass deployment")
            else:
                logger.error("No group Id %s found, reset not required" % group_id)
    except ClientError as e:
        logger.error("Error: %s" % e)
        result = cfnresponse.FAILED
    logger.info(
        "Returning response of: %s, with result of: %s" % (result, responseData)
    )
    sys.stdout.flush()
    cfnresponse.send(event, context, result, responseData)
