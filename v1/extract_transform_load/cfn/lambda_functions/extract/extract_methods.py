"""Different methods for extraction to be used by the calling process"""

import time
import queue
import threading
import logging

import redis
import can

# Intermediate data format read from CAN Bus is: "timestamp.nnnn 0xID 0xDATA"
CANBUS_DATA_FORMAT = "{} {:02X} {}"

log = logging.getLogger()
log.setLevel("INFO")

r = redis.Redis(host="localhost", port=6379, db=0)


# These functions are specific to the Kvaser data logger. replace the logic
# with the query and persist data logic as needed.
def canbus_kvaser_query_pids(bus, pids):
    """Send queries for all PID's of interest"""
    for i in pids:
        bus.send(pids[i])
    return


def canbus_kvaser_bus_request(bus, pids):
    """Request parameters of interest every 20ms"""
    while True:
        canbus_kvaser_query_pids(bus, pids)
        time.sleep(0.1)


def canbus_kvaser_bus_response(bus, queue):
    """Continiously read the CAN Bus and queue entries"""
    for msg in bus:
        # Only log common OBD-II parameters:
        if msg.arbitration_id == 0x7E8:
            queue.put(
                CANBUS_DATA_FORMAT.format(
                    time.time(), msg.arbitration_id, msg.data.hex().upper()
                )
            )


def canbus_kvaser_persist_data(queue):
    """Read data from queue and persist"""
    total_events = 0
    while True:
        data = queue.get()
        total_events += 1
        r.rpush("extract_queue", data)
        if total_events % 100 == 0:
            log.info(f"Processed {total_events} events since starting")


def canbus_kvaser(queue, PIDS):
    """Use Kvaser canlib via python-can to query PIDS of interest
       This runs until the calling process terminates"""

    # This is specific to the Kvaser series of data loggers

    bus = can.Bus(interface="kvaser", channel=0, receive_own_messages=True)
    # Setup threads to interact with CAN Bus, read data, and persist to data store
    worker_canbus_request = threading.Thread(
        target=canbus_kvaser_bus_request, args=[bus, PIDS]
    )
    worker_canbus_response = threading.Thread(
        target=canbus_kvaser_bus_response, args=[bus, queue]
    )
    worker_persist = threading.Thread(target=canbus_kvaser_persist_data, args=[queue])
    # Start workers in reverse order, so messages aren't missed
    worker_persist.start()
    worker_canbus_response.start()
    worker_canbus_request.start()

    while True:
        # Loop forever, check in every minute
        time.sleep(60)


# Main "extract" function used, see description below.
def file_playback(queue, filename):
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
                    r.rpush("extract_queue", entry)
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
                    r.rpush("extract_queue", entry)
                if total_events % 100 == 0:
                    log.info(f"Processed {total_events} events since starting")
