# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from CfnResponse import send, SUCCESS, FAILED
from DeleteLogGroup import handler as deleteloggroup_hander
import logging as log


def handler(event, context):
    try:
        if "ResourceProperties" in event and "Action" in event["ResourceProperties"]:
            action = event["ResourceProperties"]["Action"]
            log.info(f"Action: {action}")
            if action == "DeleteLogGroup":
                res = deleteloggroup_hander(event, context)
            else:
                raise Exception("Unknown action")

            send(event, context, SUCCESS, {}, res["PhysicalResourceId"])
        else:
            raise Exception("Action not specified")
    except Exception as e:
        log.error(e)
        send(event, context, FAILED, {}, reason=str(e))
