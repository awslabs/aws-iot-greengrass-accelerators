"""
Create AWS IoT thing, certificate and policy to be used by Greengrass CloudFormation resources
"""

import json
import os
import logging
import time
import boto3
from botocore.exceptions import ClientError

__copyright__ = (
    "Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved."
)
__license__ = "MIT-0"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_iot_thing_certificate_policy(thing_name: str):
    """Create IoT thing, AWS IoT generated certificate and private key,
       IoT policy for thing, and IAM role for Greengrass Group role
    """

    iot_client = boto3.client("iot")

    # Create thing
    while True:
        try:
            # Create thing
            response = iot_client.create_thing(thingName=thing_name)
            thing_arn = response["thingArn"]
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.create_thing() (will retry) for thing {thing_name}, error: {e}"
            )
            time.sleep(2)
            continue

    # Create certificate and private key
    while True:
        try:
            # Create key and certificate, stash the values for later
            response = iot_client.create_keys_and_certificate(setAsActive=True)
            certificate_arn = response["certificateArn"]
            certificate_pem = response["certificatePem"]
            private_key = response["keyPair"]["PrivateKey"]
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.create_keys_and_certificate() (will retry) for thing {thing_name}, error: {e}"
            )
            time.sleep(2)
            continue

    # Create AWS IoT policy for use by Greengrass Core (the thing)
    gg_core_policy = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "iot:*", "Resource": "*"},
                {"Effect": "Allow", "Action": "greengrass:*", "Resource": "*"},
            ],
        }
    )

    while True:
        try:
            # Create policy
            response = iot_client.create_policy(
                policyName=thing_name + "-full-access", policyDocument=gg_core_policy
            )
            iot_policy = response["policyName"]
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.create_policy() (will retry) for thing {thing_name}, error: {e}"
            )
            time.sleep(2)
            continue

    # Thing and certificate created, attach thing <-> certificate <-> policy
    # Policy to certificate
    while True:
        try:
            iot_client.attach_principal_policy(
                policyName=iot_policy, principal=certificate_arn
            )
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.attach_principal_policy() policy to cert (will retry) for thing {thing_name}, error: {e}"
            )
            time.sleep(2)
            continue
    # Thing to certificate
    while True:
        try:
            iot_client.attach_thing_principal(
                thingName=thing_name, principal=certificate_arn
            )
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.attach_principal_policy() thing to cert (will retry) for thing {thing_name}, error: {e}"
            )
            time.sleep(2)
            continue

    # Describe the general ATS endpoint
    while True:
        try:
            response = iot_client.describe_endpoint(endpointType="iot:Data-ATS")
            endpoint_ats = response["endpointAddress"]
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.describe_endpoint() to obtain iot:Data-ATS endpoint for thing {thing_name}, error: {e}"
            )
            time.sleep(2)
            continue

    # Build return dictionary
    ret = {
        "thingArn": thing_arn,
        "certificateArn": certificate_arn,
        "certificatePem": certificate_pem,
        "keyPem": private_key,
        "endpointDataAts": endpoint_ats,
    }

    return ret


def delete_iot_thing_certificate_policy(thing_name: str):
    """Delete IoT thing, AWS IoT generated certificate and private key,
       IoT policy for thing, and IAM role for Greengrass Group role
    """

    iot_client = boto3.client("iot")

    # Query thing for certificate
    while True:
        try:
            response = iot_client.list_thing_principals(thingName=thing_name)
            certificate_arn = response["principals"][0]
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.list_thing_principals() for thing {thing_name}, error: {e}"
            )
            return False

    # Query first certificate for attached thing(s) and policies, save each
    while True:
        try:
            response = iot_client.list_attached_policies(target=certificate_arn)
            policy = response["policies"][0]["policyName"]
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.list_attached_policies() for certificate Arn {certificate_arn}, error: {e}"
            )
            return False

    # Detach certificate from policy
    while True:
        try:
            response = iot_client.detach_policy(
                policyName=policy, target=certificate_arn
            )
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.detach_policy() for certificate and policy, certificate:  {certificate_arn}, error: {e}"
            )
            return False

    # Detach certificate from thing
    while True:
        try:
            response = iot_client.detach_thing_principal(
                thingName=thing_name, principal=certificate_arn
            )
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.detach_policy() for certificate and thing, certificate:  {certificate_arn}, error: {e}"
            )
            return False

    # Deactivate and delete certificate
    while True:
        try:
            iot_client.update_certificate(
                certificateId=certificate_arn.split("/")[-1], newStatus="INACTIVE"
            )
            iot_client.delete_certificate(certificateId=certificate_arn.split("/")[-1])
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.update_certificate() to set certificate {certificate_arn} to inactive state, error: {e}"
            )
            return False

    # Delete Policy
    while True:
        try:
            response = iot_client.delete_policy(policyName=policy)
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.delete_policy() to delete policy, policy name: {policy}, error: {e}"
            )
            return False

    # Delete Thing
    while True:
        try:
            response = iot_client.delete_thing(thingName=thing_name)
            break
        except ClientError as e:
            logger.warning(
                f"Error calling iot.delete_thing() to delete thing, thing name: {thing_name}, error: {e}"
            )
            return False

    # If all steps have been processed, return True
    return True


def main(event, context):
    import logging as log
    import cfnresponse

    log.getLogger().setLevel(log.INFO)

    # NOTE: All ResourceProperties passed will uppercase the first letter
    #       of the property and leave the rest of the case intact.

    physical_id = event["ResourceProperties"]["PhysicalId"]
    cfn_response = cfnresponse.SUCCESS

    try:
        log.info("Input event: %s", event)

        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            # Operations to perform during Create, then return response_data
            response = create_iot_thing_certificate_policy(
                thing_name=event["ResourceProperties"]["GreengrassCoreName"]
            )
            response_data = {
                "thingArn": response["thingArn"],
                "certificateArn": response["certificateArn"],
                "certificatePem": response["certificatePem"],
                "privateKeyPem": response["keyPem"],
                "endpointDataAts": response["endpointDataAts"],
            }
        elif event["RequestType"] == "Update":
            # Operations to perform during Update, then return NULL for response data
            response_data = {}
        else:
            if not delete_iot_thing_certificate_policy(
                thing_name=event["ResourceProperties"]["GreengrassCoreName"]
            ):
                # there was an error, alert
                cfn_response = cfnresponse.FAILED
            response_data = {}
        cfnresponse.send(event, context, cfn_response, response_data, physical_id)

    except Exception as e:
        log.exception(e)
        # cfnresponse error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
