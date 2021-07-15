# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import urllib3
import json

http = urllib3.PoolManager()
SUCCESS = "SUCCESS"
FAILED = "FAILED"


def send(
    event,
    context,
    responseStatus,
    responseData,
    physicalResourceId=None,
    noEcho=False,
    reason=None,
):
    responseUrl = event["ResponseURL"]

    responseBody = {}
    responseBody["Status"] = responseStatus
    if not reason:
        responseBody["Reason"] = (
            "See the details in CloudWatch Log Stream: " + context.log_stream_name
        )
    else:
        responseBody["Reason"] = reason
    responseBody["PhysicalResourceId"] = physicalResourceId or context.log_stream_name
    responseBody["StackId"] = event["StackId"]
    responseBody["RequestId"] = event["RequestId"]
    responseBody["LogicalResourceId"] = event["LogicalResourceId"]
    responseBody["NoEcho"] = noEcho
    responseBody["Data"] = responseData

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {"content-type": "", "content-length": str(len(json_responseBody))}

    try:

        response = http.request(
            "PUT", responseUrl, body=json_responseBody.encode("utf-8"), headers=headers
        )
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))
