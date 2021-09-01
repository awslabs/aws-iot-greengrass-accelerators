# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# In its current form, this code is not fit for production workloads.

import threading
import can
import os
import time
import argparse
import logging

import awsiot.greengrasscoreipc
from awsiot.greengrasscoreipc.model import (
    PublishToTopicRequest,
    PublishMessage,
    BinaryMessage
)

TIMEOUT = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

parser = argparse.ArgumentParser()
parser.add_argument("--publish-topic", required=True)
args = parser.parse_args()

ipc_client = awsiot.greengrasscoreipc.connect()

# Main "extract" function used, see description below.
def file_playback(filename):
    """Plays back a pre-recorded file of CAN Bus events at the same time
       rate they were recorded. When the final entry is persisted, start again
       from the beginning of the file.
    """
    while True:
        total_events = 0
        # Iterate over file forever
        with open(filename, "r") as f:
            previous_time = 0.0
            for entry in f:
                total_events += 1
                if previous_time == 0.0:  # First entry in file
                    previous_time = float(entry.split(" ")[0])
                    # Replace timestamp with current time and put on extract list
                    entry = (
                        str(time.time())
                        + " "
                        + entry.split(" ")[1]
                        + " "
                        + entry.split(" ")[2].strip("\n")
                    )
                    obd_two_send_message(entry)
                else:  # all other entries use delta from previous event
                    event_time = float(entry.split(" ")[0])
                    time.sleep(event_time - previous_time)
                    previous_time = event_time
                    # Replace timestamp with current time and put on extract list
                    entry = (
                        str(time.time())
                        + " "
                        + entry.split(" ")[1]
                        + " "
                        + entry.split(" ")[2].strip("\n")
                    )
                    obd_two_send_message(entry)
                if total_events % 100 == 0:
                    logger.info(f"Processed {total_events} events since starting")

# Main "extract" function used, see description below.
def obd_two_send_message(message_string):
    request = PublishToTopicRequest()
    request.topic = args.publish_topic
    publish_message = PublishMessage()
    publish_message.binary_message = BinaryMessage()
    publish_message.binary_message.message = bytes(message_string, "utf-8")
    request.publish_message = publish_message
    operation = ipc_client.new_publish_to_topic()
    operation.activate(request)