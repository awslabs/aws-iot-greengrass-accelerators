#!/usr/bin/env python
"""Extracts messages from CAN Bus interface and save to file"""

import os
import time
import threading
import queue
import zipfile

import can
from can import Message

# List of OBD-II parameter Ids to query
PIDS = {
    "vehicle_speed": Message(
        arbitration_id=0x7DF,
        extended_id=False,
        data=[0x2, 0x1, 0xD, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "engine_load": Message(
        arbitration_id=0x7DF,
        extended_id=False,
        data=[0x2, 0x1, 0x4, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "coolant_temp": Message(
        arbitration_id=0x7DF,
        extended_id=False,
        data=[0x2, 0x1, 0x5, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "engine_rpm": Message(
        arbitration_id=0x7DF,
        extended_id=False,
        data=[0x2, 0x1, 0xC, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "throttle_position": Message(
        arbitration_id=0x7DF,
        extended_id=False,
        data=[0x2, 0x1, 0x11, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "ambient_air_temperature": Message(
        arbitration_id=0x7DF,
        extended_id=False,
        data=[0x2, 0x1, 0x46, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
}
# Intermediate format is: "timestamp.nnnn ID DATA"
CANBUS_DATA_FORMAT = "{} {:02X} {}"


def bus_request(bus, pids, run_event):
    """Request parameters of interest on the bus every 20ms, bus_response reads the responses"""
    while run_event.is_set():
        for i in pids:
            try:
                bus.send(pids[i], timeout=0.02)
            except can.interfaces.kvaser.canlib.CANLIBError:
                bus.flush_tx_buffer()
                print("error")
        # Pause 50ms between queries
        time.sleep(0.05)


def bus_response(bus, q):
    """
    Continiously read the CAN Bus and queues entries of interest,
    filtered to OBD-II class messages
    """
    for msg in bus:
        # Only log common OBD-II parameters:
        if msg.arbitration_id == 0x7E8:
            q.put(
                CANBUS_DATA_FORMAT.format(
                    time.time(), msg.arbitration_id, msg.data.hex().upper()
                )
            )


def persist_data(q, run_event):
    """Read data from queue and persist to local file"""
    total_events = 0
    f = open("events.txt", "a", buffering=512)
    while run_event.is_set():
        try:
            event = q.get(False)
            f.write(f"{event}\n")
            total_events += 1
            if total_events % 200 == 0:
                print(f"read and written {total_events} events")
        except queue.Empty:
            # No work to process, continue
            pass
    f.close()


# Common elements used by all extract methods
message_queue = queue.Queue()

# Connect to data source
# This is specific to the Kvaser Leaf Light v2 data logger,
# replace with specifics for your CAN Bus device
bus = can.Bus(interface="kvaser", channel=0, receive_own_messages=True)

# Setup threads to interact with CAN Bus, read data, and persist to data store
run_event = threading.Event()
run_event.set()

worker_canbus_request = threading.Thread(
    target=bus_request, args=[bus, PIDS, run_event]
)
worker_canbus_response = threading.Thread(
    target=bus_response, args=[bus, message_queue]
)
worker_persist = threading.Thread(target=persist_data, args=[message_queue, run_event])
# Start workers in reverse order, so messages aren't missed
worker_persist.start()
worker_canbus_response.start()
worker_canbus_request.start()

try:
    while True:
        # Until keyboard interrupt
        pass
except KeyboardInterrupt:
    print("Closing threads")
    run_event.clear()
    worker_canbus_request.join()
    worker_persist.join()
    print("Threads successfully closed")
    os._exit(0)
