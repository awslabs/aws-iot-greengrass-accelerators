import time
import traceback
import argparse
import logging

import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    SubscribeToTopicRequest,
    SubscriptionResponseMessage,
    QOS,
    PublishToIoTCoreRequest,
    BinaryMessage
)

TIMEOUT = 10
qos = QOS.AT_LEAST_ONCE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

parser = argparse.ArgumentParser()
parser.add_argument("--request-topic", required=True)
parser.add_argument("--publish-topic", required=True)
args = parser.parse_args()

ipc_client = awsiot.greengrasscoreipc.connect()
                    
class StreamHandler(client.SubscribeToTopicStreamHandler):
    def __init__(self):
        super().__init__()

    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        try:
            message_string = str(event.binary_message.message, "utf-8")

            send_obd2_json_to_cloud(message_string)
            
        except:
            traceback.print_exc()

    def on_stream_error(self, error: Exception) -> bool:
        # Handle error.
        return True  # Return True to close stream, False to keep stream open.

    def on_stream_closed(self) -> None:
        # Handle close.
        pass

def send_obd2_json_to_cloud(message_json_string):
    request = PublishToIoTCoreRequest()
    request.topic_name = args.publish_topic
    request.payload = bytes(message_json_string, "utf-8")
    request.qos = qos
    operation = ipc_client.new_publish_to_iot_core()
    operation.activate(request)

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
        time.sleep(1)
        
    subscribe_operation.close()

if __name__ == "__main__":
    main()