# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT
"""An high level API to work with the Greengrass v2 SDK.

It provides a simple API abstraction to publish and subscribe messages to MqttProxy and PubSub IPC
providing both synchronous and asynchronous methods.

To use:
from greengrassipcsdk import IPCIotCore, QOS
client = IPCIotCore()

def handler(topic, message):
    print(topic)
    print(message.decode('utf8))

client.subscribe('topic/test', QOS.AT_MOST_ONCE, handler)

client.publish('topic/test', bytes('Hello', 'utf8'), QOS.AT_MOST_ONCE)
"""

from threading import Timer

from awsiot.greengrasscoreipc import connect

class BaseClient:
    def __init__(self, ipc_client=None, timeout=10):
        if ipc_client == None:
            ipc_client = connect()
        self._ipc_client = ipc_client
        self._timeout = timeout

    def _sync_error_handler(self, error: Exception) -> None:
        """Internal handler that raises an error thrown by the subscriber handler
        """
        raise error

    def _dummy_loop(self):
            self._timer = Timer(interval=10, function=_dummy_loop)
            self._timer.start()

    def start_loop(self):
        """Start a waiting loop for the subscription
        """
        self._timer = Timer(interval=10, function=_dummy_loop)
        self._timer.start()

    def stop_loop(self):
        self._timer.cancel()



