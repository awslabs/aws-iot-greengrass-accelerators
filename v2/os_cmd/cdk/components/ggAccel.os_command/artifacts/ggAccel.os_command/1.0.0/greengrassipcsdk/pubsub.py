# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT

import typing
from threading import Thread
from typing import Callable
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
    BinaryMessage,
    JsonMessage,
    PublishToTopicRequest,
    SubscribeToTopicRequest,
    SubscriptionResponseMessage,
    PublishMessage,
)
from . import BaseClient

import concurrent.futures


class _BinarySubscribeHandler(client.SubscribeToTopicStreamHandler):
    def __init__(
        self,
        handler: Callable[[str, bytes], None],
        error_handler: Callable[[Exception], None],
    ):
        self._handler = handler
        self._error_handler = error_handler

    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        msg = event.binary_message.message
        t = Thread(target=self._handler, args=["pubsub", msg])
        t.start()

    def on_stream_error(self, error: Exception) -> bool:
        t = Thread(target=self._error_handler, args=[error])
        t.start()
        return True

    def on_stream_closed(self) -> None:
        pass


class _JsonSubscribeHandler(client.SubscribeToTopicStreamHandler):
    def __init__(
        self,
        handler: Callable[[str, object], None],
        error_handler: Callable[[Exception], None],
    ):
        self._handler = handler
        self._error_handler = error_handler

    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        msg = event.json_message.message
        t = Thread(target=self._handler, args=["pubsub", msg])
        t.start()

    def on_stream_error(self, error: Exception) -> bool:
        t = Thread(target=self._error_handler, args=[error])
        t.start()
        return True

    def on_stream_closed(self) -> None:
        pass


class Client(BaseClient):
    def publish_binary_async(
        self, topic: str, message: bytes
    ) -> concurrent.futures.Future:
        """Returns a Future

        Publishes a message on a topic with the given qos.
        """

        request = PublishToTopicRequest()
        publish_message = PublishMessage()
        publish_message.binary_message = BinaryMessage()
        publish_message.binary_message.message = message
        request.topic = topic
        request.publish_message = publish_message
        operation = self._ipc_client.new_publish_to_topic()
        operation.activate(request)
        future = operation.get_response()
        return future

    def publish_binary(self, topic: str, message: bytes):
        """Publishes a message synchronously to AWS IoT Core via Greengrass connection

        Throws an exception if the publish fails
        """
        try:
            future = self.publish_binary_async(topic, message)
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def publish_json_async(
        self, topic: str, message: dict
    ) -> concurrent.futures.Future:
        """Returns a Future

        Publishes a message on a topic with the given qos.
        """

        request = PublishToTopicRequest()
        publish_message = PublishMessage()
        publish_message.json_message = JsonMessage()
        publish_message.json_message.message = message
        request.topic = topic
        request.publish_message = publish_message
        operation = self._ipc_client.new_publish_to_topic()
        operation.activate(request)
        future = operation.get_response()
        return future

    def publish_json(self, topic: str, message: dict):
        """Publishes a message synchronously to AWS IoT Core via Greengrass connection

        Throws an exception if the publish fails
        """
        try:
            future = self.publish_json_async(topic, message)
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def subscribe_binary_async(
        self,
        topic: str,
        handler: Callable[[str, bytes], None],
        error_handler: Callable[[Exception], None],
    ) -> concurrent.futures.Future:
        """Subscribes to a topic asynchronously with a given QoS.

        All received messages are sent to the handler.
        Unhandled exceptions in the handler code will be sent to the error_handler
        """

        request = SubscribeToTopicRequest()
        request.topic = topic
        _handler = _BinarySubscribeHandler(handler, error_handler)
        operation = self._ipc_client.new_subscribe_to_topic(_handler)
        operation.activate(request)
        future = operation.get_response()
        return future

    def subscribe_binary(self, topic: str, handler: Callable[[str, bytes], None]):
        """
        Subscribes to a topic asynchronously with a given QoS.

        All received messages are sent to the handler.
        Throws an exception if there are unhandled exceptions in the handler code.
        """
        try:
            future = self.subscribe_binary_async(
                topic, handler, self._sync_error_handler
            )
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def subscribe_json_async(
        self,
        topic: str,
        handler: Callable[[str, object], None],
        error_handler: Callable[[Exception], None],
    ) -> concurrent.futures.Future:
        """Subscribes to a topic asynchronously with a given QoS.

        All received messages are sent to the handler.
        Unhandled exceptions in the handler code will be sent to the error_handler
        """

        request = SubscribeToTopicRequest()
        request.topic = topic
        _handler = _JsonSubscribeHandler(handler, error_handler)
        operation = self._ipc_client.new_subscribe_to_topic(_handler)
        operation.activate(request)
        future = operation.get_response()
        return future

    def subscribe_json(self, topic: str, handler: Callable[[str, object], None]):
        """
        Subscribes to a topic asynchronously with a given QoS.

        All received messages are sent to the handler.
        Throws an exception if there are unhandled exceptions in the handler code.
        """
        try:
            future = self.subscribe_json_async(topic, handler, self._sync_error_handler)
            future.result(self._timeout)
        except Exception as ex:
            raise ex
