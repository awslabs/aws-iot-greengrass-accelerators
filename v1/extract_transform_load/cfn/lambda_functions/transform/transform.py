"""
   Transforms CAN BUS messages from Redis extract_queue and places on load_queue

   In this example, vehicle speed, ambient temperature, and throttle position are
   calculated (average, min, and max values) and then placed on the load_queue.
   Also, all individual messages are transformed and placed on the load_queue.
"""
import os
import json
import time
import logging

import redis

# redistimeseries now part of redis-py >=4.0.0
# from redistimeseries.client import Client as RedisTimeSeries

# Formulas to perform transforms on messages
import transformation_list as transforms

log = logging.getLogger()
# log.setLevel("INFO")

# Setup Redis and events of interest to track
r = redis.Redis(host="localhost", port=6379, db=0)
# Create TimeSeries object
rts = r.ts()
if not r.exists("vehicle_speed"):
    rts.create("vehicle_speed", retention_msecs=300000, labels={"Time": "Series"})
if not r.exists("throttle_position"):
    rts.create("throttle_position", retention_msecs=300000, labels={"Time": "Series"})
if not r.exists("ambient_air_temperature"):
    rts.create(
        "ambient_air_temperature", retention_msecs=300000, labels={"Time": "Series"}
    )

# Track all messages on extract queue to only send every 1 second
msg_time_last_sent = {}


def ts_val(rts, key, from_time, to_time, agg):
    """Return aggregation type from Redis time series db"""
    val = float(
        rts.range(
            key,
            from_time=from_time,
            to_time=to_time,
            aggregation_type=agg,
            bucket_size_msec=from_time - to_time,
        )[0][1]
    )
    return val


# Main Lambda entry point
def handler(event, context):
    """Changes state of running Lambda through incoming message"""
    # Place code here to change globally read variables by the worker threads
    return


####### This global code is executed once at Lambda/Greengrass startup #######
##############################################################################

total_events = 0
# load_events = 0
load_velocity_sec = 1
timer_for_average = time.time()
while True:
    msg = r.blpop("extract_queue")
    # Convert CAN Bus message to JSON
    converted_message = transforms.obd2_convert(msg[1])

    # Update moving averages if message matches
    redis_ts = int(float(converted_message["Timestamp"]) * 1000)
    if converted_message["Pid"] == "VehicleSpeed":
        rts.add("vehicle_speed", redis_ts, converted_message["Value"])
    elif converted_message["Pid"] == "ThrottlePosition":
        rts.add("throttle_position", redis_ts, converted_message["Value"])
    elif converted_message["Pid"] == "AmbientAirTemperature":
        rts.add("ambient_air_temperature", redis_ts, converted_message["Value"])
    # Create time series messages on average duration every 30 seconds
    cur_time = time.time()
    if (cur_time - timer_for_average) > 30:
        from_time = int(timer_for_average * 1000)
        to_time = int(cur_time * 1000)
        msg = {
            "VehicleSpeed": {
                "Avg": round(
                    ts_val(rts, "vehicle_speed", from_time, to_time, "avg"), 2
                ),
                "Min": round(
                    ts_val(rts, "vehicle_speed", from_time, to_time, "min"), 2
                ),
                "Max": round(
                    ts_val(rts, "vehicle_speed", from_time, to_time, "max"), 2
                ),
                "Units": "km/h",
            },
            "ThrottlePosition": {
                "Avg": round(
                    ts_val(rts, "throttle_position", from_time, to_time, "avg"), 2
                ),
                "Min": round(
                    ts_val(rts, "throttle_position", from_time, to_time, "min"), 2
                ),
                "Max": round(
                    ts_val(rts, "throttle_position", from_time, to_time, "max"), 2
                ),
                "Units": "%",
            },
            "AmbientAirTemperature": {
                "Avg": round(
                    ts_val(rts, "ambient_air_temperature", from_time, to_time, "avg"), 2
                ),
                "Min": round(
                    ts_val(rts, "ambient_air_temperature", from_time, to_time, "min"), 2
                ),
                "Max": round(
                    ts_val(rts, "ambient_air_temperature", from_time, to_time, "max"), 2
                ),
                "Units": "Celsius",
            },
            "Timestamp": cur_time,
            "Source": "Rolling Average",
        }
        r.rpush("load_queue", json.dumps(msg))
        timer_for_average = time.time()

    # Place message on load queue, rate-limited to 1 message per second
    r.rpush("load_queue", json.dumps(converted_message))
    total_events += 1
    # if converted_message["Pid"] in msg_time_last_sent:
    #     # Check if timestamp is more than reporting duration
    #     cur_time = time.time()
    #     total_events += 1
    #     if (
    #         cur_time - msg_time_last_sent[converted_message["Pid"]]
    #     ) > load_velocity_sec:
    #         r.rpush("load_queue", json.dumps(converted_message))
    #         msg_time_last_sent[converted_message["Pid"]] = cur_time
    #         load_events += 1
    # else:
    #     # First time message seen, place on load queue
    #     r.rpush("load_queue", json.dumps(converted_message))
    #     msg_time_last_sent[converted_message["Pid"]] = time.time()
    #     total_events += 1

    # Report on function status
    if (total_events % 100 == 0) and total_events > 0:
        log.info(f"Read {total_events} from extract_queue")
    # if (load_events % 100 == 0) and (load_events > 0):
    #     log.info(f"Placed {load_events} to load_queue")
