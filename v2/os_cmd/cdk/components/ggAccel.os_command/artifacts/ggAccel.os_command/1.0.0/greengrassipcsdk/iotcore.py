# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT

from threading import Thread
from typing import Callable
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
    QOS,
    PublishToIoTCoreRequest,
    SubscribeToIoTCoreRequest,
    IoTCoreMessage
)

import concurrent.futures

from . import BaseClient

class _MqttSubscribeHandler(client.SubscribeToIoTCoreStreamHandler):
    
    def __init__(self, handler: Callable[[str, bytes], None], error_handler: Callable[[Exception], None] ):
        self._handler = handler
        self._error_handler = error_handler

    def on_stream_event(self, event: IoTCoreMessage) -> None:
        msg = event.message
        t = Thread(target=self._handler, args=[msg.topic_name, msg.payload])
        t.start()

    def on_stream_error(self, error: Exception)-> bool:
        t = Thread(target=self._error_handler, args=[error])
        t.start()
        return True

    def on_stream_closed(self) -> None:
        pass


class Client(BaseClient):

    def publish_async(self, topic: str, message: bytes, qos: QOS) -> concurrent.futures.Future:
        """Returns a Future

        Publishes a message on a topic with the given qos. 
        """

        request = PublishToIoTCoreRequest()
        request.topic_name = topic
        request.payload = message
        request.qos = qos
        operation = self._ipc_client.new_publish_to_iot_core()
        operation.activate(request)
        future = operation.get_response()
        return future

    def publish(self, topic: str, message: bytes, qos: QOS):
        """Publishes a message synchronously to AWS IoT Core via Greengrass connection

        Throws an exception if the publish fails
        """
        try:
            future = self.publish_async(topic, message, qos)
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def subscribe_async(self, topic: str, qos: QOS, handler: Callable[[str, bytes], None], error_handler: Callable[[Exception], None]) -> concurrent.futures.Future:
        """Subscribes to a topic asynchronously with a given QoS. 

        All received messages are sent to the handler. 
        Unhandled exceptions in the handler code will be sent to the error_handler
        """
        
        request = SubscribeToIoTCoreRequest()
        request.topic_name = topic
        request.qos = qos
        _handler = _MqttSubscribeHandler(handler, error_handler)
        operation = self._ipc_client.new_subscribe_to_iot_core(_handler)
        operation.activate(request)
        future = operation.get_response()
        return future

    def subscribe(self, topic: str, qos: QOS, handler: Callable[[str, bytes], None]):
        """
        Subscribes to a topic asynchronously with a given QoS. 

        All received messages are sent to the handler. 
        Throws an exception if there are unhandled exceptions in the handler code.
        """
        try:
            future = self.subscribe_async(topic, qos, handler, self._sync_error_handler)
            future.result(self._timeout)
        except Exception as ex:
            raise ex
    
    