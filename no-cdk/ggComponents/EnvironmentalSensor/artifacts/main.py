
# Copyright 2022 Amazon.com, Inc. and its affiliates. All Rights Reserved.

# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at

# http://aws.amazon.com/asl/

# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.


import json
import datetime
import time
import sys
import traceback
import random

from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2
from awsiot.greengrasscoreipc.model import (
    UnauthorizedError,
    IoTCoreMessage,
    QOS
)


class EnvironmentalSensor(object):
    # this class simulates a combined sensor producing the following payload
    # {'timestamp': epoch,
    # 'temperature': 444, 'tempUnit': 'C/F',
    # 'humidity': 0..100,
    # 'luminosity':  0..40000, 'lumUnit: 'Lux'

    def __init__(self):
        self._sensorID = "envS000001"
        self._topic = "test/envSensor/" + self._sensorID
        self.sampling_period = 5
        self.lastsample = {'timestamp':0, 'temperature':0, 'tempUnit':'C', 'humidity':0, 'luminosity':0, 'lumUnit':'Lux'}

    def read_sample(self):
# in Windows datetime.datetime.now().strftime('%s') gives an error
        self.lastsample['timestamp'] = int(datetime.datetime.utcnow().timestamp()) 
        self.lastsample['temperature'] = round(random.uniform(-20, 50))
        self.lastsample['humidity'] = round(random.uniform(0, 100))
        self.lastsample['luminosity'] = round(random.uniform(0, 40000))
        return self.lastsample

def on_stream_event(event: IoTCoreMessage) -> None:
    try:
        message_string = str(event.message.payload, "utf-8")
        #topic = event.message.topic
        print('Received new message :' , message_string)
    except:
        traceback.print_exc()


def on_stream_error(error: Exception) -> bool:
    print('Received a stream error.', file=sys.stderr)
    traceback.print_exc()
    return False  # Return True to close stream, False to keep stream open.


def on_stream_closed() -> None:
    print('Subscribe to topic stream closed.')


if __name__ == '__main__':

    ipc_client = GreengrassCoreIPCClientV2()

    topic = 'test/calibration/envSensor'
    try:
        operation = ipc_client.subscribe_to_iot_core( topic_name = topic, 
                                                      qos=QOS.AT_LEAST_ONCE, 
                                                      on_stream_event = on_stream_event,
                                                      on_stream_error = on_stream_error,
                                                      on_stream_closed = on_stream_closed)
        print('Successfully subscribed to topic: %s', topic)
    
    except UnauthorizedError:
        print('Unauthorized error while subscribing to topic: ' +
              topic, file=sys.stderr)
        traceback.print_exc()
        exit(1)
    except Exception:
        print('Exception occurred', file=sys.stderr)
        traceback.print_exc()
        exit(1)

    sensor = EnvironmentalSensor()
    i = 0
    while True:
        sample = sensor.read_sample()
        print(f"Publishing sample no.: {i} to IoT core, {sample}")
        try:
            message_string = json.dumps(sample)
            ipc_client.publish_to_iot_core( topic_name=sensor._topic, qos=QOS.AT_LEAST_ONCE, payload=message_string)
        except:
            traceback.print_exc()
            exit(1)

        time.sleep(sensor.sampling_period )
        i = i + 1
