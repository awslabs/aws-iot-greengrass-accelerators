# Greengrass lambda source -sensor source
import os
import json
import asyncio
from threading import Thread, Lock
from time import sleep, time
from random import gauss
import greengrasssdk
import flask
from flask import request, jsonify
from greengrasssdk.stream_manager import (
    StreamManagerClient,
    ReadMessagesOptions,
    NotEnoughMessagesException,
    MessageStreamDefinition,
    StrategyOnFull,
    ExportDefinition,
    IoTAnalyticsConfig,
    InvalidRequestException,
    StreamManagerException,
    Persistence,
)

lock = Lock()
generate_sensor_data = True
channel_name = os.environ["STREAM_MANAGER_CHANNEL"]

app = flask.Flask(__name__)
client = StreamManagerClient()
try:
    client.create_message_stream(
        MessageStreamDefinition(
            name="LocalDataStream",  # Required.
            max_size=268435456,  # Default is 256 MB.
            stream_segment_size=16777216,  # Default is 16 MB.
            time_to_live_millis=None,  # By default, no TTL is enabled.
            strategy_on_full=StrategyOnFull.OverwriteOldestData,  # Required.
            persistence=Persistence.File,  # Default is File.
            flush_on_write=False,  # Default is false.
            export_definition=ExportDefinition(
                iot_analytics=[
                    IoTAnalyticsConfig(
                        identifier="RawData",
                        iot_channel=channel_name,
                        # iot_msg_id_prefix="test",
                        # batch_size=1,
                        # batch_interval_millis=1000,
                        # priority=1
                    )
                ]
            ),
        )
    )
except StreamManagerException as e:
    print(f"Error creating message stream: {e}")
    while True:
        print(f"StreamManagerException loop for: {e}")
        sleep(5)
except Exception as e:
    print(f"General exception error: {e}")
    while True:
        print(f"General exception loop for: {e}")
        sleep(5)


@app.route("/api/v1/sensor/data/enable", methods=["GET"])
def api_sensor_data_enable():
    global generate_sensor_data
    lock.acquire()
    generate_sensor_data = True
    lock.release()
    return jsonify({"response": "sensor data enabled"})


@app.route("/api/v1/sensor/data/disable", methods=["GET"])
def api_sensor_data_disable():
    global generate_sensor_data
    lock.acquire()
    generate_sensor_data = False
    lock.release()
    return jsonify({"response": "sensor data disabled"})


@app.route("/api/v1/sensor/data/status", methods=["GET"])
def api_sensor_data_status():
    global generate_sensor_data
    lock.acquire()
    status = generate_sensor_data
    lock.release()
    return jsonify({"response": f"sensor data generation is set to {status}"})


def simulated_data():
    """Randomly generate data and timestamp"""
    hertz = float("%.2f" % (gauss(1000, 2)))
    temperature = float("%.2f" % (gauss(80, 4)))
    timestamp = float("%.4f" % (time()))
    return {"hertz": hertz, "temperature": temperature, "timestamp": timestamp}


def api_server():
    """Run and process API requests as separate thread"""
    Thread(
        target=app.run, kwargs={"host": "0.0.0.0", "port": 8180, "threaded": True}
    ).start()


def sensor_data_server():
    """ Generates and publishes sensor data if enabled
        Data generation is at 10 messages per second, with each message containing
        values for temperature and humidity.
    """

    while True:
        lock.acquire()
        if generate_sensor_data:
            lock.release()
            data = simulated_data()
            print(json.dumps(data))
            try:
                client.append_message(stream_name="LocalDataStream", data=json.dumps(data).encode())
            except Exception as e:
                print(f"Error appending: {e}")
            sleep(0.1)
            continue
        lock.release()
        # Nothing to do, wait a bit before checking again
        sleep(0.05)


def app_startup():
    """Startup all separate threads"""
    print("Starting API")
    api_thread = Thread(target=api_server, args=[])
    api_thread.start()
    print("Starting simulated sensor data")
    sensor_data_thread = Thread(target=sensor_data_server)
    sensor_data_thread.start()


app_startup()
print("boo yah!")


def main(event, context):
    """Called per invoke, we should never see this (long running Lambda)"""

    return
