# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# In its current form, this code is not fit for production workloads.

import sys
import datetime
import time
import json
import traceback
import argparse
import logging

import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    SubscribeToTopicRequest,
    SubscriptionResponseMessage,
    PublishToTopicRequest,
    PublishMessage,
    BinaryMessage
)
import transformation_list as transforms

TIMEOUT = 10

parser = argparse.ArgumentParser()
parser.add_argument("--request-topic", required=True)
parser.add_argument("--result-topic", required=True)
parser.add_argument("--log-level", required=True)
args = parser.parse_args()

logger = logging.getLogger()

levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
level = levels.get(args.log_level.lower())
logging.basicConfig(level=level)

ipc_client = awsiot.greengrasscoreipc.connect()

class StreamHandler(client.SubscribeToTopicStreamHandler):
    def __init__(self):
        super().__init__()

    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        try:
            message_string = str(event.binary_message.message, "utf-8")

            #Transform
            converted_message = transforms.obd2_convert(message_string)
            
            #Send
            send_obd2_json(converted_message)
                
        except:
            traceback.print_exc()

    def on_stream_error(self, error: Exception) -> bool:
        # Handle error.
        return True  # Return True to close stream, False to keep stream open.

    def on_stream_closed(self) -> None:
        # Handle close.
        pass

def send_obd2_json(message_json):
    message_json_string = json.dumps(message_json).replace('"', '\"')
    request = PublishToTopicRequest()
    request.topic = args.result_topic
    publish_message = PublishMessage()
    publish_message.binary_message = BinaryMessage()
    publish_message.binary_message.message = bytes(message_json_string, "utf-8")
    request.publish_message = publish_message
    operation = ipc_client.new_publish_to_topic()
    operation.activate(request)
    logger.debug(message_json_string)
    # future = operation.get_response()
    
def setup_subscribtion():
    request = SubscribeToTopicRequest()
    request.topic = args.request_topic
    handler = StreamHandler()
    operation = ipc_client.new_subscribe_to_topic(handler) 
    future = operation.activate(request)
    future.result(TIMEOUT)
    return operation


def main() -> None:
    """Code to execute from script"""

    logger.info(f"Arguments: {args}")
    subscribe_operation = setup_subscribtion()

    while True:
        # Keep app open and running
        time.sleep(1)
        
    subscribe_operation.close()


if __name__ == "__main__":
    main()