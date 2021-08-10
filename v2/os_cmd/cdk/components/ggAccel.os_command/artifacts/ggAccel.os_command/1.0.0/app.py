"""
Listen for incoming command requests and publish the results onto another topic

--request-topic - topic to listen for commands
--response-topic - topic to publish the standard output of the command

Command message structure (JSON):
{
    "command": "ls -l /tmp",
    "txid": "12345ABC",
    "format": "json|text",
    "timeout": 10
}
- `command` - full string to pass to shell interpreter
- `txid` - unique id to track status of message, returned as part of response.
  Note: New commands cannot use the id of any in-flight operations that have not completed.
- `format` - Optional, default json. Format of response message. JSON is serialized string,
  text is key value formatted with response as everything after the RESPONSE: line.
- `timeout` - Optional, default is 10 seconds. Amount of time for the command to complete.

- Total payload size must be less than 128KiB in size, including request topic.
- Command will run as default ggc_user unless changed in the recipe file

Response message structure (JSON):
{
    "txid": "12345ABC",
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

# response_template = {"txid": None, "return_code": None, "response": None}

TIMEOUT = 10
RESPONSE_FORMAT = "json"
MSG_INVALID_JSON = "Request message was not a valid JSON obect"
MSG_MISSING_ATTRIBUTE = "The attributes 'txid' and 'command' missing from request"
MSG_TIMEOUT = f"Command timed out, limit of {TIMEOUT} seconds"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Register SIGTERM for shutdown of container
def signal_handler(signal, frame) -> None:
    logger.info(f"Received {signal}, exiting")
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

parser = argparse.ArgumentParser()
parser.add_argument("--request-topic", required=True)
parser.add_argument("--response-topic", required=True)
args = parser.parse_args()


# Main process to receive and deliver messages to event handlers


def handler(topic, message: json) -> None:
    """Main function to receive and process commands"""

    resp = {}
    operation_timeout = TIMEOUT
    response_format = RESPONSE_FORMAT
    logger.info(f"Processing message received on topic {topic}")

    # validate message and attributes
    try:
        command = json.loads(message.decode("utf-8"))
        # Verify required keys are provided
        if not all(k in command for k in ("txid", "command")):
            resp["response"] = MSG_MISSING_ATTRIBUTE
            resp["return_code"] = 255
            client = iotcore.Client()
            client.publish(
                args.response_topic,
                bytes(json.dumps(resp), encoding="utf-8"),
                iotcore.QOS.AT_MOST_ONCE,
            )
            logger.error(f"{MSG_MISSING_ATTRIBUTE} for message: {message}")
            return
        # check for and update optional settings
        for k in command:
            if k.lower() == "timeout" and isinstance(command[k], (int, float)):
                operation_timeout = command[k]
            elif k.lower() == "format" and (
                any(format in command[k] for format in ["json", "text"])
            ):
                response_format = command[k].lower()
    except json.JSONDecodeError as e:
        resp["response"] = MSG_INVALID_JSON
        resp["return_code"] = 255
        client = iotcore.Client()
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
    client = iotcore.Client(timeout=operation_timeout)
    try:
        output = subprocess.run(
            command["command"],
            timeout=operation_timeout,
            capture_output=True,
            shell=True,
        )
        if output.returncode == 0:
            resp["response"] = output.stdout.decode("utf-8")
        else:
            resp["response"] = output.stderr.decode("utf-8")
        resp["txid"] = command["txid"]
        resp["return_code"] = output.returncode
    except subprocess.TimeoutExpired:
        resp["response"] = MSG_TIMEOUT
        logger.error(
            f"Comand took longer than {operation_timeout} seconds for message: {message}"
        )

    # Publish response
    if response_format == "json":
        command_response = bytes(json.dumps(resp), encoding="utf-8")
    elif response_format == "text":
        command_response = bytes(
            f"TX_ID: {command['txid']}\nRETURN_CODE: {resp['return_code']}\nRESPONSE:\n{resp['response']}",
            encoding="utf-8",
        )
    client.publish(
        args.response_topic,
        command_response,
        iotcore.QOS.AT_MOST_ONCE,
    )


def main() -> None:
    """Code to execute from script"""

    logger.info(f"Arguments: {args}")
    client = iotcore.Client()
    client.subscribe(args.request_topic, iotcore.QOS.AT_MOST_ONCE, handler)

    while True:
        # Keep app open and running
        time.sleep(1)


if __name__ == "__main__":
    main()
