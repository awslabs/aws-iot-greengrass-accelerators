"""
Custom resource function to create/delete a GreengrassGroupRole with specific permissions
"""

import json
import os
import logging
import time
import boto3
from botocore.exceptions import ClientError

__copyright__ = (
    "Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved."
)
__license__ = "MIT-0"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_greengrass_group_role(role_name: str, policy: str):
    """Creates a Greengrass Group Role with Greengrass managed role plus the additional
    policy statements from JSON policy statements
    """

    iam_client = boto3.client("iam")
    assume_role_policy_document = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "greengrass.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )

    # Create IAM role and attach policies (managed and provided)
    try:
        # Create role and allow Greengrass to assume
        response = iam_client.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_document
        )
        role_arn = response["Role"]["Arn"]
    except ClientError as e:
        logger.warning(
            f"Error calling iam.create_role() for role {role_name}, error: {e}"
        )
        return False

    try:
        # Apply general resource policy (limited iot, greengrass, and other services)
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGreengrassResourceAccessRolePolicy",
        )
    except ClientError as e:
        logger.warning(
            f"Error calling iam_client.attach_role_policy() for role {role_name}, error: {e}"
        )
        return False

    try:
        # Apply inline policy to role
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="AdditionalGreengrassGroupPermissions",
            PolicyDocument=json.dumps(policy),
        )
    except ClientError as e:
        logger.warning(
            f"Error calling iam_client.put_role_policy() for role {role_name}, error: {e}"
        )
        return False
    return role_arn


def delete_greengrass_group_role(role_name: str):
    """Delete the GreengrassGroupRole"""

    iam_client = boto3.client("iam")

    try:
        # Get and delete attached inline policies
        policies = iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]
        for policy in policies:
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy)
    except ClientError as e:
        logger.warning(
            f"Error deleting inline policies for role {role_name}, error: {e}"
        )
        return False

    try:
        # Get and delete attached managed policies
        policies = iam_client.list_attached_role_policies(RoleName=role_name)[
            "AttachedPolicies"
        ]
        for policy in policies:
            iam_client.detach_role_policy(
                RoleName=role_name, PolicyArn=policy["PolicyArn"]
            )
    except ClientError as e:
        logger.warning(
            f"Error deleting managed policies for role {role_name}, error: {e}"
        )
        return False

    try:
        # Delete the role
        iam_client.delete_role(RoleName=role_name)
    except ClientError as e:
        logger.warning(
            f"Error calling iam_client.delete_role() for role {role_name}, error: {e}"
        )
        return False
    return True


def main(event, context):
    import logging as log
    import cfnresponse

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
            # Operations to perform during Create, then return response_data
            role_arn = create_greengrass_group_role(
                role_name=event["ResourceProperties"]["RoleName"],
                policy=event["ResourceProperties"]["RolePolicy"],
            )
            if role_arn:
                response_data = {"roleArn": role_arn}
                logger.info(f"Created and returning roleArn: {role_arn}")
            else:
                logger.error("should not get here")
                cfn_response = cfnresponse.FAILED
                response_data = {}
        elif event["RequestType"] == "Update":
            # Operations to perform during Update, then return NULL for response data
            response_data = {}
        else:
            # Delete request
            # Operations to perform during Delete, then return response_data
            if not delete_greengrass_group_role(
                role_name=event["ResourceProperties"]["RoleName"]
            ):
                cfn_response = cfnresponse.FAILED
            response_data = {}
        cfnresponse.send(event, context, cfn_response, response_data, physical_id)

    except Exception as e:
        log.exception(e)
        # cfnresponse error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
