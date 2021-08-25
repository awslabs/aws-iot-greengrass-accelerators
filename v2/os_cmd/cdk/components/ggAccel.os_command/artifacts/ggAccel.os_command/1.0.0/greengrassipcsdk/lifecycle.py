# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT

import typing
from threading import Thread
from typing import Callable
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
   ComponentUpdatePolicyEvents,
   DeferComponentUpdateRequest,
   LifecycleState,
   SubscribeToComponentUpdatesRequest,
   UpdateStateRequest
)

import concurrent.futures
from . import BaseClient

class _LifecycleEventsHandler(client.SubscribeToComponentUpdatesStreamHandler):
    
    def __init__(self, ipc_client, pre_evt_handler: Callable[[str, bool], None], post_evt_handler: Callable[[str, bool], (int, str)], error_handler: Callable[[Exception], None], timeout: int = 10):
        self._pre_handler = pre_evt_handler
        self._post_handler = post_evt_handler
        self._error_handler = error_handler
        self._ipc_client = ipc_client
        self._timeout = timeout

    def on_stream_event(self, event: ComponentUpdatePolicyEvents) -> None:
        t = Thread(target=self._handler_wrapper, args=[event])
        t.start()
           
    def _handler_wrapper(self, event: ComponentUpdatePolicyEvents) -> None:
        """ Internal thread wrapper to invoke the pre and post handlers

        On post the handler publishes a DeferComponentUpdateRequest
        """
        if event.pre_update_event != None:
            self._pre_handler(event.pre_update_event.deployment_id, event.pre_update_event.is_ggc_restarting)
        elif event.post_update_event != None:   
            delay_ms, msg = self._post_handler(event.post_update_event.deployment_id)
            if delay_ms < 0:
                delay_ms = 0

            request = DeferComponentUpdateRequest(deployment_id=event.post_update_event.deployment_id, message=msg, recheck_after_ms=delay_ms)
            operation = self._ipc_client.new_defer_component_update()
            operation.activate(request)
            operation.get_result(self._timeout)

    def on_stream_error(self, error: Exception)-> bool:
        t = Thread(target=self._error_handler, args=[error])
        t.start()
        return True

    def on_stream_closed(self) -> None:
        pass


class Client(BaseClient):

    def update_state_async(self, state: LifecycleState) -> concurrent.futures.Future:
        """Returns a Future

        Update the running state of the component
        """

        request = UpdateStateRequest(state = state)
        operation = self._ipc_client.new_update_state()
        operation.activate(request)
        future = operation.get_response()
        return future

    def update_state(self, state: LifecycleState):
        """Updates the running state of the component

        Throws an exception if the update fails
        """
        try:
            future = self.update_state_async(state)
            future.result(self._timeout)
        except Exception as ex:
            raise ex

    def subscribe_to_component_updates_async(self, pre_evt_handler: typing.Optional(Callable[[str, bool], None]), post_evt_handler: typing.Optional(Callable[[str], (int, str)]), error_handler: Callable[[Exception], None]) -> concurrent.futures.Future:
        """Subscribes pre and/or post component update events 

        The pre events allow the component to get notified if Greengrass is restarting
        The post events allow the component to defer the update by returning a delay and an optional message
        """
        
        request = SubscribeToComponentUpdatesRequest()
        _handler = _LifecycleEventsHandler(self._ipc_client, pre_evt_handler=pre_evt_handler, post_evt_handler=post_evt_handler, error_handler=error_handler, timeout=self._timeout)
        operation = self._ipc_client.new_subscribe_to_component_updates(_handler)
        operation.activate(request)
        future = operation.get_response()
        return future

    def subscribe_to_component_updates(self, pre_evt_handler: typing.Optional(Callable[[str, bool], None]), post_evt_handler: typing.Optional(Callable[[str], (int, str)])) -> None:
        """Subscribes pre and/or post component update events 

        The pre events allow the component to get notified if Greengrass is restarting
        The post events allow the component to defer the update by returning a delay and an optional message
        """
        try:
            future = self.subscribe_to_component_updates_async(pre_evt_handler=pre_evt_handler, post_evt_handler=post_evt_handler, error_handler=self._sync_error_handler)
            future.result(self._timeout)
        except Exception as ex:
            raise ex
    
