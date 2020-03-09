# Greengrass lambda source -sensor source
import json
import logging
from threading import Thread, Lock
from time import sleep, time
from random import gauss
import greengrasssdk
import flask
from flask import request, jsonify

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.WARN)

client = greengrasssdk.client("iot-data")
lock = Lock()
generate_sensor_data = True
app = flask.Flask(__name__)


@app.route("/api/v1/sensor/data/enable", methods=["GET"])
def api_sensor_data_enable():
    """Enable generation of sensor data"""
    global generate_sensor_data
    lock.acquire()
    generate_sensor_data = True
    lock.release()
    return jsonify({"response": "sensor data enabled"})


@app.route("/api/v1/sensor/data/disable", methods=["GET"])
def api_sensor_data_disable():
    """Disables generation of sensor data"""
    global generate_sensor_data
    lock.acquire()
    generate_sensor_data = False
    lock.release()
    return jsonify({"response": "sensor data disabled"})


@app.route("/api/v1/sensor/data/status", methods=["GET"])
def api_sensor_data_status():
    """Returns current status of sensor data generation"""
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
            # Publish data to Lambda Producer directly
            try:
                client.publish(
                    topic="sensor_data", qos=0, payload=json.dumps(data).encode("utf-8")
                )
            except Exception as e:
                logger.error(f"Error appending: {e}")
            sleep(0.05)
            continue
        else:
            lock.release()
            # Data generation disabled, pause before checking again
            sleep(0.05)


def app_startup():
    """Startup all separate threads"""
    logger.info("Starting API")
    api_thread = Thread(target=api_server, args=[])
    api_thread.start()
    logger.info("Starting simulated sensor data")
    sensor_data_thread = Thread(target=sensor_data_server)
    sensor_data_thread.start()


app_startup()


def main(event, context):
    """Called per invoke, we should never see this (long running Lambda)"""
    return
