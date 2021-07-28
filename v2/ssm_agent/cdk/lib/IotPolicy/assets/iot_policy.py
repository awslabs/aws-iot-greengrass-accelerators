# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import logging as logger
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger.getLogger().setLevel(logger.INFO)


def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def create_resources(
    iot_policy: str,
    iot_policy_name: str,
    certificate_arn: str,
):
    """Create AWS IoT policy and attach it to referenced certificate."""
    c_iot = get_aws_client("iot")

    result = {}

    # Create policy
    try:
        response = c_iot.create_policy(
            policyName=iot_policy_name, policyDocument=iot_policy
        )
        result["IotPolicyArn"] = response["policyArn"]
    except ClientError as e:
        logger.error(f"Error creating policy {iot_policy_name}, {e}")
        sys.exit(1)

    # attach cert-pol
    try:
        c_iot.attach_policy(policyName=iot_policy_name, target=certificate_arn)
    except ClientError as e:
        logger.error(
            f"Error attaching certificate {certificate_arn} to policy {iot_policy_name}, {e}"
        )
        sys.exit(1)

    except ClientError as e:
        logger.error(f"Error creating secure string parameters, {e}")
        sys.exit(1)

    return result


def delete_resources(certificate_arn: str, iot_policy_name: str):
    """Detach certificate from policy then delete the IoT policy"""

    c_iot = get_aws_client("iot")

    result = {}

    # delete policy (prune versions, detach from targets)
    # delete all non active policy versions
    try:
        response = c_iot.list_policy_versions(policyName=iot_policy_name)
        for version in response["policyVersions"]:
            if not version["isDefaultVersion"]:
                c_iot.delete_policy_version(
                    policyName=iot_policy_name, policyVersionId=version["versionId"]
                )
    except ClientError as e:
        logger.error(
            f"Unable to delete policy versions for policy {iot_policy_name}, {e}"
        )

    # Detach any targets (things or principals from policy)
    try:
        response = c_iot.list_targets_for_policy(policyName=iot_policy_name)
        for target in response["targets"]:
            c_iot.detach_policy(policyName=iot_policy_name, target=target)
    except ClientError as e:
        logger.error(f"Unable to detach targets from policy {iot_policy_name}, {e}")

    # delete policy
    try:
        c_iot.delete_policy(policyName=iot_policy_name)
    except ClientError as e:
        logger.error(f"Unable to delete policy {iot_policy_name}, {e}")

    return result


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
                iot_policy=props["IotPolicy"],
                iot_policy_name=props["IoTPolicyName"],
                certificate_arn=props["CertificateArn"],
            )

            # set response data (PascalCase key)
            response_data = {
                "IotPolicyArn": resp["IotPolicyArn"],
            }
            physical_resource_id = response_data["IotPolicyArn"]
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            resp = delete_resources(
                certificate_arn=props["CertificateArn"],
                iot_policy_name=props["IoTPolicyName"],
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