"""Extracts messages from CAN Bus interface and persists to Extract queue"""

import os
import queue

import can
from can import Message

import pidlist
from extract_methods import canbus_kvaser, file_playback

PIDS = pidlist.PIDS


def persist_data(queue):
    """Read data from queue and persist"""
    while True:
        data = queue.get()
        print(f"Data read: {data}")


# Main Lambda entry point
def handler(event, context):
    """Changes state of running Lambda through incoming message"""
    # Place code here to change globally read variables by the worker threads
    return


####### This global code is executed once at Lambda/Greengrass startup #######
##############################################################################

# Common elements used by all extract methods
message_queue = queue.Queue()

# Uncomment one of the methods below to perform the
# extraction of data. Each function will take control until Greengrass restarts
# the Lambda function.

#### Read from Kvaser data logger
# canbus_kvaser(message_queue, PIDS)

### Read from pre-recorded playback file. Loops to beginning at completion
# events1.txt contains only filtered OBD-II PIDs captured every 100ms
# events2.txt contains complete capture of CAN Bus (2010 Subaru Outback) and
# the requested OBD-II PIDs (at 100ms resolution)
file_playback(message_queue, "events1.txt")
