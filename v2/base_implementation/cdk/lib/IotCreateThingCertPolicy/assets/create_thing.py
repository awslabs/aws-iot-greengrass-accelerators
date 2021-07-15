# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
import logging as log
import boto3
import botocore

# import jinja2

log.getLogger().setLevel(log.INFO)

temp = {
    "LogicalResourceId": "CreateIoTThingIoTCreateThingCertPolicy3E20AAFB",
    "RequestId": "4515b51d-d7b2-449b-92b0-f38eca234840",
    "RequestType": "Create",
    "ResourceProperties": {
        "CreateCertificate": "true",
        "IotPolicy": {
            "Statement": [
                {"Action": "iot:*", "Effect": "Allow", "Resource": "*"},
                {"Action": "greengrass:*", "Effect": "Allow", "Resource": "*"},
            ],
            "Version": "2012-10-17",
        },
        "ServiceToken": "arn:aws:lambda:us-west-2:904880203774:function:test1-CreateIoTThingIoTCreateThingframeworkonEvent-DjP6xw1aDvpI",
        "StackName": "test1",
        "ThingName": "foo-test",
    },
    "ResourceType": "AWS::CloudFormation::CustomResource",
    "ResponseURL": "https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A904880203774%3Astack/test1/4c7187f0-e4e3-11eb-ba16-02184d4f065d%7CCreateIoTThingIoTCreateThingCertPolicy3E20AAFB%7C4515b51d-d7b2-449b-92b0-f38eca234840?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20210714T203908Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIA54RCMT6SKBOPMYGJ%2F20210714%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Signature=edec84d86edbfa5ea2b47b69773a16b16f13e7c731d9405595daaf28f198e07b",
    "ServiceToken": "arn:aws:lambda:us-west-2:904880203774:function:test1-CreateIoTThingIoTCreateThingframeworkonEvent-DjP6xw1aDvpI",
    "StackId": "arn:aws:cloudformation:us-west-2:904880203774:stack/test1/4c7187f0-e4e3-11eb-ba16-02184d4f065d",
}


def get_aws_client(name):
    return boto3.client(
        name,
        region_name=os.environ["REGION"],
        config=botocore.config.Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def create_thing(
    thing_name: str, create_certificate: bool = False, iot_policy: dict = None
):
    """Create AWS IoT thing and optionally attach to a created certificate and policy.
        Returns the Arns for the values and a Parameter Store Arn for the private key

    :param thing_name: thingName to create, defaults to None
    :type thing_name: str, required
    :param create_certificate: Create AWS vended certificate if True, defaults to False
    :type create_certificate: bool, optional
    :param iot_policy: AWS IoT policy to be parsed and created, defaults to None
    :type iot_policy: dict, optional
    """

    return


def handler(event, context):
    log.info("Received event: %s", event)
    log.info("Environment: %s", dict(os.environ))
    props = event["ResourceProperties"]
    try:
        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            log.info("Request CREATE")
            # call stuff

            # set response data (PascalCase key)
            response_data = {}
        elif event["RequestType"] == "Update":
            log.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            log.info("Request DELETE")
            response_data = {}
        else:
            log.info("Should not get here in normal cases - could be REPLACE")

        output = {"PhysicalResourceId": props["ThingName"], "Data": response_data}
        log.info("Output from Lambda: %s", json.dumps(output, indent=2))
    except Exception as e:
        log.exception(e)