# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT

# Copyright 2021 Amazon.com.
# SPDX-License-Identifier: MIT

import typing
from threading import Thread
from typing import Callable
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc import connect
from awsiot.greengrasscoreipc.model import (
   GetSecretValueRequest,
   SecretValue
)

import concurrent.futures

from . import BaseClient

class Client(BaseClient):

    def get_secret_async(self, secretId: str, versionId: typing.Optional(str), versionStage: typing.Optional(str)) -> concurrent.futures.Future:
        """Returns a Future

        Gets the values of a secret
        """

        request = GetSecretValueRequest(secret_id=secretId, version_id=versionId, version_stage=versionStage)
        operation = self._ipc_client.new_get_secret_value()
        operation.activate(request)
        future = operation.get_response()
        return future

    def get_secret(self, secretId: str, versionId: typing.Optional(str), versionStage: typing.Optional(str)) -> SecretValue:
        """Get the value of a secret. Return a SecretValue

        Throws an exception if the update fails
        """
        try:
            future = self.update_state_async(secretId=secretId, versionId=versionId, versionStage=versionStage)
            response = future.result(self._timeout)
            return response.secret_value
        except Exception as ex:
            raise ex

