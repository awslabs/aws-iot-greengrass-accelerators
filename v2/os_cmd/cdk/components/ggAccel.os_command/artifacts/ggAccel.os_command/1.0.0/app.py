"""
Listen for incoming command requests and publish the results onto another topic

--request-topic - topic to listen for commands
--response-topic - topic to publish the standard output of the command

Command message structure (JSON):
{
    "command": "ls -l /tmp",
    "message_id": "12345ABC"
}
- Total payload size must be less than 128KiB in size, including request topic.
- Command will run as default ggc_user unless changed in the recipe file

Response message structure (JSON):
{
    "message_id": "12345ABC",
    "return_code": 0,
    "response": "total 17688\n-rw-r--r--   1 ggc_user  staff     8939 Apr 30 16:37 README.md\n"
}
- If response is greater than 128KiB, exit_code will be set to 255 and "payload too long" response.
- Malformed request with set exit_code  to 255 and "malformed request/missing transaction id/etc" response.

"""

import signal
import sys
import time
import logging
import argparse
import json
import subprocess
from greengrassipcsdk import iotcore

response_template = {"message_id": None, "return_code": None, "response": None}

TIMEOUT = 10
MSG_INVALID_JSON = "Request message was not a valid JSON obect"
MSG_MISSING_ATTRIBUTE = "The attributes 'message_id' and 'command' missing from request"
MSG_TIMEOUT = f"Command timed out, limit of {TIMEOUT} seconds"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Register SIGTERM for shutdown of container
def signal_handler(signal, frame):
    logger.info(f"Received {signal}, exiting")
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

parser = argparse.ArgumentParser()
parser.add_argument("--request-topic", required=True)
parser.add_argument("--response-topic", required=True)
args = parser.parse_args()

client = iotcore.Client()


# Main process to receive and deliver messages to event handlers


def handler(topic, message):
    """receive and process JSON command"""

    resp = response_template

    # validate message and attributes
    try:
        command = json.loads(message.decode("utf-8"))
        if not all(k in command for k in ("message_id", "command")):
            resp["response"] = MSG_MISSING_ATTRIBUTE
            resp["return_code"] = 255
            client.publish(
                args.response_topic,
                bytes(json.dumps(resp), encoding="utf-8"),
                iotcore.QOS.AT_MOST_ONCE,
            )
            logger.error(f"{MSG_MISSING_ATTRIBUTE} for message: {message}")
            return
    except json.JSONDecodeError as e:
        resp["response"] = MSG_INVALID_JSON
        resp["return_code"] = 255
        client.publish(
            args.response_topic,
            bytes(json.dumps(resp), encoding="utf-8"),
            iotcore.QOS.AT_MOST_ONCE,
        )
        logger.error(f"{MSG_INVALID_JSON} for message: {message}")
        return
    except Exception as e:
        raise e

    # Run command and process results
    try:
        output = subprocess.run(
            command["command"], timeout=TIMEOUT, capture_output=True, shell=True
        )
        if output.returncode == 0:
            resp["response"] = output.stdout.decode("utf-8")
        else:
            resp["response"] = output.stderr.decode("utf-8")
        resp["message_id"] = command["message_id"]
        resp["return_code"] = output.returncode
    except subprocess.TimeoutExpired:
        resp["response"] = MSG_TIMEOUT
        logger.error(f"Comand took too long for message: {message}")

    # Publish response
    client.publish(
        args.response_topic,
        bytes(json.dumps(resp), encoding="utf-8"),
        iotcore.QOS.AT_MOST_ONCE,
    )


client.subscribe(args.request_topic, iotcore.QOS.AT_MOST_ONCE, handler)

while True:
    # Keep app open and running
    time.sleep(1)
