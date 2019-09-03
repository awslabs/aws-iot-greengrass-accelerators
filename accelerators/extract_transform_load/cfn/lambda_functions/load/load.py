"""Loads messages from Load queue and sends to AWS services in the same region"""

import os
import json
import time
import logging

import redis
import boto3
import greengrasssdk
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

config = Config(
    retries=dict(max_attempts=10)
)  # set to large amount in case of connection outage

# Track all messages on load queue to only send every 1 second
msg_time_last_sent = {}

r = redis.Redis(host="localhost", port=6379, db=0)
client = boto3.client("firehose", config=config)
gg = greengrasssdk.client("iot-data")

# Main Lambda entry point
def handler(event, context):
    """Changes state of running Lambda through incoming message"""
    # Place code here to change globally read variables by the worker threads
    return


def put_firehose(client, msg):
    """Put record on Firehose, block until complete"""
    while True:
        try:
            client.put_record(
                DeliveryStreamName=os.environ["DELIVERY_STREAM"],
                Record={"Data": (json.dumps(msg) + "\n").encode()},
            )
            return
        except ClientError as e:
            # Connection to cloud lost, retry until connection is restored
            print(f"Error: {e}, looping until connectivity restored")
            continue


####### This global code is executed once at Lambda/Greengrass startup #######
##############################################################################
last_alert_time = time.time()
load_velocity_sec = 1
while True:
    msg = json.loads(r.blpop("load_queue")[1])
    if msg["Source"] == "Rolling Average":
        # Place on topic
        gg.publish(
            topic=os.environ["CORE_NAME"] + "/telemetry", payload=json.dumps(msg)
        )
    elif msg["Source"] == "OBD-II":
        # Firehose check - only emit messages once per define velocity
        if msg["Pid"] in msg_time_last_sent:
            # Check if timestamp is more than reporting duration
            cur_time = time.time()
            if (cur_time - msg_time_last_sent[msg["Pid"]]) > load_velocity_sec:
                # send to firehose
                put_firehose(client, msg)
                msg_time_last_sent[msg["Pid"]] = cur_time
        else:
            # First time message seen, send to Firehose
            put_firehose(client, msg)
            msg_time_last_sent[msg["Pid"]] = time.time()

        # Publish for local use. Add subscription to consume from Lambda or device
        gg.publish(topic="rt", payload=json.dumps(msg))

    elif msg["Source"] == "CAN Bus":
        # If the message is generic CAN Bus (not OBD-II specific)
        # place into Firehose and trigger an alert message every second
        put_firehose(client, msg)
        if (time.time() - last_alert_time) > 1:
            alert_msg = {
                "Source": "Unknown Parameter",
                "Info": "A non-OBD-II CAN Bus message was received, the hex-encoded details of the last triggered message are in the 'Msg' key",
                "Msg": msg,
            }
            gg.publish(
                topic=os.environ["CORE_NAME"] + "/alert", payload=json.dumps(alert_msg)
            )
            last_alert_time = time.time()
