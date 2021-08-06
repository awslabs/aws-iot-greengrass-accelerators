# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT

import typing
from . import _asyncio_wrapper
import asyncio
from threading import Thread
from typing import Callable
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
    GetConfigurationRequest,
    SendConfigurationValidityReportRequest,
    UpdateConfigurationRequest,
    SubscribeToConfigurationUpdateRequest,
    SubscribeToValidateConfigurationUpdatesRequest,
    ConfigurationUpdateEvents,
    ConfigurationUpdateEvent,
    ValidateConfigurationUpdateEvent,
    ValidateConfigurationUpdateEvents,
    ConfigurationValidityReport,
    ConfigurationValidityStatus
)

import concurrent.futures

from . import BaseClient

class _ConfigurationUpdateStreamHandler(client.SubscribeToConfigurationUpdateStreamHandler):
    
    def __init__(self, handler: Callable[[ConfigurationUpdateEvent], None], error_handler: Callable[[Exception], None] ):
        self._handler = handler
        self._error_handler = error_handler

    def on_stream_event(self, event: ConfigurationUpdateEvents) -> None:
        update_event = event.configuration_update_event
        t = Thread(target=self._handler, args=[update_event.component_name, "/"+"/".join(update_event.key_path)])
        t.start()

    def on_stream_error(self, error: Exception)-> bool:
        t = Thread(target=self._error_handler, args=[error])
        t.start()
        return True

    def on_stream_closed(self) -> None:
        pass

class _ValidateConfigurationStreamHandler(client.SubscribeToValidateConfigurationUpdatesStreamHandler):
    def __init__(self, ipc_client, handler: Callable[[typing.Dict[str, typing.Any]], bool], error_handler: Callable[[Exception], None], timeout: int ):
        self._handler = handler
        self._error_handler = error_handler
        self._ipc_client = ipc_client
        self._timeout = timeout

    def on_stream_event(self, event: ValidateConfigurationUpdateEvents) -> None:
        '''For each event we call a wrapper method that invokes the validation handler and 
        publishes the report with the status to the IPC
        '''
        validate_event = event.validate_configuration_update_event
        t = Thread(target=self.response_wrapper, args=[validate_event.configuration])
        t.start()

    def on_stream_error(self, error: Exception)-> bool:
        t = Thread(target=self._error_handler, args=[error])
        t.start()
        return True

    def on_stream_closed(self) -> None:
        pass

    def response_wrapper(self, event: ValidateConfigurationUpdateEvent) -> None:
        (accepted, message) = self._handler(event.configuration)
        request = SendConfigurationValidityReportRequest()
        report = ConfigurationValidityReport()
        report.deployment_id = event.deployment_id
        report.message = message
        
        if accepted:
            report.status = ConfigurationValidityStatus.ACCEPTED
        else:
            report.status = ConfigurationValidityStatus.REJECTED
        request.configuration_validity_report = report
        operation = self._ipc_client.new_send_configuration_validity_report_operation()
        future = operation.activate(request)
        try:
            future.get_result(self._timeout)
        except ex:
            raise ex

class Client(BaseClient):
    """Create an client to interact with the Component Configuration APIs.

    Optionally one can pass a GreengrassCoreIPCClient and a timeout for the async operations
    """

    def get_configuration_async(self, component:str, key_path:str) -> asyncio.Future:
        """Gets the component configuration at keypath

        keypath is a JSON path /key1/key2/0
        Return the a Future that resolves to a GetConfigurationResponse object
        """

        request = GetConfigurationRequest()
        request.component_name = component
        request.key_path = key_path
        operation = self._ipc_client.new_get_configuration()
        operation.activate(request)
        future = operation.get_response()
        return future

    def get_configuration(self, component:str, key_path:str) -> typing.Any:
        """Publishes a message synchronously to AWS IoT Core via Greengrass connection

        Throws an exception if the publish fails
        """
        try:
            future = self.get_configuration_async(component=component, key_path=key_path)
            result = future.result(self._timeout)
            return result.value
        except Exception as ex:
            raise ex

    def update_configuration_async(self, component:str, key_path:str, value: typing.Dict[str, typing.Any]) -> concurrent.futures.Future:
        """Updates the component configuration at keypath by merging the value

        keypath is a JSON path

        Return the a Future that resolves to a GetConfigurationResponse object
        """

        request = UpdateConfigurationRequest()
        request.component_name = component
        request.key_path = key_path.split("/")
        request.value_to_merge = value
        operation = self._ipc_client.new_update_configuration()
        operation.activate(request)
        future = operation.get_response()
        return future

    def update_configuration(self, component:str, key_path:str, value: typing.Dict[str, typing.Any]) -> None:
        """Updates the component configuration at keypath by merging the value

        keypath is a JSON path

        Throws an exception if the publish fails
        """
        try:
            future = self.update_configuration_async(component=component, key_path=key_path, value=value)
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def subscribe_to_validate_requests_async(self, handler: Callable[[typing.Dict[str, typing.Any]], bool], error_handler: Callable[[Exception], None]) -> concurrent.futures.Future:
        """Subscribes to configuration validation requests. 

        The handler should accept a Dict object as parameter and return a True or False. 
        Unhandled exceptions in the handler code will be sent to the error_handler
        """
        
        request = SubscribeToValidateConfigurationUpdatesRequest()
        _handler = _ValidateConfigurationStreamHandler(handler, error_handler, timeout=self._timeout)
        operation = self._ipc_client.new_subscribe_to_validate_configuration_updates(_handler)
        operation.activate(request)
        future = operation.get_response()
        return future

    def subscribe_to_validate_requests(self, handler: Callable[[typing.Dict[str, typing.Any]], bool]):
        """Subscribes to configuration validation requests. 

        The handler should accept a Dict object as parameter and return a True or False. 
        Throw an exception on errors
        """
        try:
            future = self.subscribe_to_validate_requests_async(handler, self._sync_error_handler)
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def subscribe_to_configuration_updates_async(self, topic: str, handler: Callable[[str, str], None], error_handler: Callable[[Exception], None]) -> concurrent.futures.Future:
        """Subscribes to configuration updates 

        Unhandled exceptions in the handler code will be sent to the error_handler

        The handler function receives two paramters: the component_name and the key_path of the configuration that changed. key_path is in JSON Path format.
        The handler is responsible to call 'get_configuration'
        """
        
        request = SubscribeToConfigurationUpdateRequest()
        _handler = _ConfigurationUpdateStreamHandler(handler, error_handler)
        operation = self._ipc_client.new_subscribe_to_configuration_updates(_handler)
        operation.activate(request)
        future = operation.get_response()
        return future

    def subscribe_to_configuration_updates(self, topic: str, handler: Callable[[str, str], None]):
        """Subscribes to configuration updates 

        The handler function receives two paramters: the component_name and the key_path of the configuration that changed. key_path is in JSON Path format.
        The handler is responsible to call 'get_configuration'
        """
        try:
            future = self.subscribe_to_configuration_updates_async(topic, handler, self._sync_error_handler)
            future.result(self._timeout)
        except Exception as ex:
            raise ex


