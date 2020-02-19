#
# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import base64
import json
import logging
import os
import re

from greengrass_machine_learning_sdk.exception import GreengrassDependencyException
from greengrass_ipc_python_sdk.ipc_facade import GreengrassServiceClient, GreengrassServiceMessage, GreengrassRuntimeException
from greengrass_machine_learning_sdk.util import ValidationUtil

PARAM_CONFIG_ID = "ConfigId"
PARAM_MODEL_INPUT = "ModelInput"
PARAM_MODEL_PREDICTION = "ModelPrediction"
PARAM_METADATA = "Metadata"

ERROR_STRING_MISSING_REQUIRED_PARAM = '{} argument of Feedback.Client.publish is a required argument but was not provided'
ERROR_STRING_INVALID_TYPE = "Argument {} must be of type {}"

CONFIG_ID_PATTERN_STRING = '^[a-zA-Z0-9][a-zA-Z0-9-]{1,62}$'
CONFIG_ID_PATTERN = re.compile(CONFIG_ID_PATTERN_STRING)


class GreengrassFeedbackException(Exception):
    '''
        Exception for Greengrass feedback error
    '''
    pass


class Client(object):
    FEEDBACK_CONNECTOR_ADDRESS_STR = 'arn:aws:lambda:{}:aws:function:MLFeedback'

    def __init__(self):
        ValidationUtil.validate_required_gg_interface()
        self._gg_service_client = GreengrassServiceClient()
        aws_region = os.environ['AWS_REGION']
        self._feedback_connector_address = self.FEEDBACK_CONNECTOR_ADDRESS_STR.format(aws_region)

    @staticmethod
    def _check_required_args(required_params, params):
        for required_param in required_params:
            if required_param not in params:
                raise ValueError(ERROR_STRING_MISSING_REQUIRED_PARAM.format(required_param))

    @staticmethod
    def _check_required_type(param, param_name, expected_type):
        if not isinstance(param, expected_type):
            raise ValueError(ERROR_STRING_INVALID_TYPE.format(param_name, expected_type.__name__))

    def publish(self, **kwargs):
        """
            :param kwargs:
                ConfigId (string): ConfigId matching a specific configuration defined in the ML Feedback connector configuration.
                ModelInput (bytes): Data that was passed to a model for inference.
                ModelPrediction (list): Representation of the model's output as a list of probabilities (float). Ex: [0.25, 0.60, 0.15].
                Metadata (dict): [Optional] Additional metadata to attach to the uploaded S3 sample as well as messages published to the /feedback/message/prediction topic.
        """

        required_params = [
            PARAM_CONFIG_ID,
            PARAM_MODEL_INPUT,
            PARAM_MODEL_PREDICTION
        ]
        Client._check_required_args(required_params, kwargs)

        config_id = kwargs.get(PARAM_CONFIG_ID)
        if not CONFIG_ID_PATTERN.match(config_id):
            raise ValueError("Parameter {} must match: {}".format(PARAM_CONFIG_ID, CONFIG_ID_PATTERN_STRING))

        # The model prediction of Image classification is a list, and that if Object Detection is a dict
        model_prediction = kwargs.get(PARAM_MODEL_PREDICTION)
        if not isinstance(model_prediction, dict) and not isinstance(model_prediction, list):
            raise ValueError(ERROR_STRING_INVALID_TYPE.format(PARAM_MODEL_PREDICTION, 'dict or list'))

        metadata = kwargs.get(PARAM_METADATA, {})
        Client._check_required_type(metadata, PARAM_METADATA, dict)

        context_json = {
            'custom': {
                PARAM_CONFIG_ID: config_id,
                PARAM_MODEL_PREDICTION: model_prediction,
                PARAM_METADATA: metadata
            }
        }
        context = base64.b64encode(json.dumps(context_json).encode('utf-8'))
        model_input = kwargs.get(PARAM_MODEL_INPUT)
        message = GreengrassServiceMessage(context, model_input)

        try:
            output = self._gg_service_client.call(self._feedback_connector_address, message)
            if output.error_response:
                raise GreengrassFeedbackException(output.error_response)
            else:
                logging.info("Successfully made request to ML Feedback connector.")
        except GreengrassRuntimeException as e:
            raise GreengrassDependencyException(e)
