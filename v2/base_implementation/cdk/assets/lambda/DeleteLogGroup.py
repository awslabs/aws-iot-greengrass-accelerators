# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import time
from awsutil import get_client

logs = get_client("logs")


def handler(event, context):
    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create(event)
    if request_type == "Update":
        return on_update(event)
    if request_type == "Delete":
        return on_delete(event)
    raise Exception("Invalid request type: %s" % request_type)


def on_delete(event):
    props = event["ResourceProperties"]
    logGroupName = props["LogGroupName"]
    try:
        logs.delete_log_group(logGroupName=logGroupName)
    except logs.exceptions.ResourceNotFoundException:
        # don't blow up if the log group has not yet been created
        pass
    return {"PhysicalResourceId": f"{logGroupName}-delete"}


def on_update(event):
    props = event["ResourceProperties"]
    logGroupName = props["LogGroupName"]
    return {"PhysicalResourceId": f"{logGroupName}-delete"}


def on_create(event):
    props = event["ResourceProperties"]
    logGroupName = props["LogGroupName"]
    return {"PhysicalResourceId": f"{logGroupName}-delete"}
