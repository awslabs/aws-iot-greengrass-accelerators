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


def create_iot_role_alias(role_name, role_alias_name, policy, policy_name):
    c_iot = get_aws_client("iot")
    c_iam = get_aws_client("iam")

    assume_role_policy_document = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "credentials.iot.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )
    # Create IAM role and allow IoT credential provider to access
    try:
        resp = c_iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy_document,
            Description="Allow Greengrass token exchange service to obtain temporary credentials",
        )
        role_arn = resp["Role"]["Arn"]
    except c_iam.exceptions.EntityAlreadyExistsException:
        logger.error(
            f"IAM role {role_name} already exists, is this a duplicate stack? Exiting"
        )
        sys.exit(1)
    except ClientError as e:
        logger.warning(
            f"Error calling iam.create_role() for role {role_name}, error: {e}"
        )

    # Attach the policy to the role
    try:
        c_iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy),
        )
    except ClientError as e:
        logger.warning(
            f"Error calling iam_client.put_role_policy() for role {role_name}, error: {e}"
        )

    # Create IoT Role alias with IAM role
    try:
        c_iot.create_role_alias(
            roleAlias=role_alias_name,
            roleArn=role_arn,
        )
    except ClientError as e:
        logger.warning(
            f"Error calling iot.create_role_alias() for role alias {role_alias_name}, error: {e}"
        )

    return role_arn


def delete_iot_role_alias(role_name, role_alias_name):
    c_iot = get_aws_client("iot")
    c_iam = get_aws_client("iam")

    # Delete the IoT role alias
    try:
        c_iot.delete_role_alias(roleAlias=role_alias_name)
    except ClientError as e:
        logger.warning(
            f"Error calling iot.delete_role_alias() for role alias {role_alias_name}, error: {e}"
        )

    # Delete attached inline policies
    try:
        policies = c_iam.list_role_policies(
            RoleName=role_name,
        )["PolicyNames"]
        for policy in policies:
            c_iam.delete_role_policy(RoleName=role_name, PolicyName=policy)
    except ClientError as e:
        logger.warning(
            f"Error deleting inline policies for role {role_name}, error: {e}"
        )
    # Delete attached managed policies
    try:
        policies = c_iam.list_attached_role_policies(
            RoleName=role_name,
        )["AttachedPolicies"]
        for policy in policies:
            c_iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])
    except ClientError as e:
        logger.warning(
            f"Error deleting inline policies for role {role_name}, error: {e}"
        )

    # Delete role
    try:
        c_iam.delete_role(RoleName=role_name)
    except ClientError as e:
        logger.warning(
            f"Error calling iam.create_role() for role {role_name}, error: {e}"
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
                role_name=props["IamRoleName"],
                role_alias_name=props["IotRoleAliasName"],
                policy=props["IamPolicy"],
                policy_name=props["PolicyName"],
            )
            # set response data (PascalCase key)
            # return IAM role arn
            response_data = {"IamRoleArn": response}
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            delete_iot_role_alias(
                role_name=props["IamRoleName"],
                role_alias_name=props["IotRoleAliasName"],
            )
            logger.info(
                f'Role alias {props["IotRoleAliasName"]} and IAM role {props["IamRoleName"]} successfully deleted'
            )
            response_data = {}
        else:
            logger.error("Should not get here in normal cases - could be REPLACE")
        # Resource id set to unique IAM role name
        output = {"PhysicalResourceId": props["IamRoleName"], "Data": response_data}
        logger.info("Output from Lambda: %s", json.dumps(output, indent=2))
    except Exception as e:
        logger.exception(e)