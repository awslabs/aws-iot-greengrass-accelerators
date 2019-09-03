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
iam = boto3.client("iam")
role_name = "greengrass_cfn_{}_ServiceRole".format(os.environ["STACK_NAME"])


def find_group_id(groupName):
    result = ""

    response = c.list_groups()
    for group in response["Groups"]:
        if groupName == group["Name"]:
            result = group["Id"]
            break

    return result


def manage_greengrass_role(cmd):
    if cmd == "CREATE":
        r = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"Service": "greengrass.amazonaws.com"},"Action": "sts:AssumeRole"}]}',
            Description="Role for CloudFormation blog post",
        )
        role_arn = r["Role"]["Arn"]
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGreengrassResourceAccessRolePolicy",
        )
        c.associate_service_role_to_account(RoleArn=role_arn)
        logger.info("Created and associated role {}".format(role_name))
    else:
        try:
            r = iam.get_role(RoleName=role_name)
            role_arn = r["Role"]["Arn"]
            c.disassociate_service_role_from_account()
            iam.delete_role(RoleName=role_name)
            logger.info("Disassociated and deleted role {}".format(role_name))
        except ClientError:
            return


def handler(event, context):
    responseData = {}
    try:
        logger.info("Received event: {}".format(json.dumps(event)))
        result = cfnresponse.FAILED
        groupName = event["ResourceProperties"]["GroupName"]
        if event["RequestType"] == "Create":
            try:
                c.get_service_role_for_account()
                result = cfnresponse.SUCCESS
            except ClientError as e:
                manage_greengrass_role("CREATE")
                logger.info("Greengrass service role created")
                result = cfnresponse.SUCCESS
        elif event["RequestType"] == "Update":
            # No action required on Update
            result = cfnresponse.SUCCESS
        elif event["RequestType"] == "Delete":
            group_id = find_group_id(groupName)
            logger.info("Group id to delete: %s" % group_id)
            if group_id:
                c.reset_deployments(Force=True, GroupId=group_id)
                result = cfnresponse.SUCCESS
                logger.info("Forced reset of Greengrass deployment")
                manage_greengrass_role("DELETE")
            else:
                logger.error("No group Id %s found, reset not required" % groupName)
    except ClientError as e:
        logger.error("Error: %s" % e)
        result = cfnresponse.FAILED
    logger.info(
        "Returning response of: %s, with result of: %s" % (result, responseData)
    )
    sys.stdout.flush()
    cfnresponse.send(event, context, result, responseData)
