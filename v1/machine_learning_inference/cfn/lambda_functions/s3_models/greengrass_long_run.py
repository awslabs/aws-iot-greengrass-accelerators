#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

# greengrass_long_run.py
# Demonstrates a simple machine learning inference
# using pre-trained model, inception_bn 
#

import logging
import greengrasssdk
import platform
from threading import Timer
import time
import sys
import os
import cv2
import json
from data_source.static_images import image_source
from inference_runtime.mxnet import load_model

# Initialize the data source
source = image_source.ImageSource()

# Initialize the inference runtime with the model
model_path = '/greengrass-machine-learning/mxnet/inception_bn/'
global_model = load_model.ImagenetModel(model_path + 'synset.txt', model_path + 'Inception-BN')

# Creating a greengrass core sdk client
client = greengrasssdk.client('iot-data')

log = logging.getLogger()
thing_name = os.environ['THINGNAME']
prediction_topic = "mli/predictions/{}".format(thing_name)

def greengrass_long_run():
    if global_model is not None:
        try:
            image, image_name = source.get_image()
            predictions = global_model.predict(image, N=1)

            # predictions = global_model.predict_from_cam()
            log.info('predictions: {}'.format(predictions))
            result=map(lambda x: {'confidence':str(x[0]),'prediction':str(x[1]),'image_name':str(os.path.basename(image_name))}, predictions)
            client.publish(topic=prediction_topic, payload=json.dumps(list(result)))
        except:
            e = sys.exc_info()[0]
            log.exception("Exception occured during prediction: {}".format(e))
    else:
        log.exception("error loading model")
            
    # Asynchronously schedule this function to be run again in 5 seconds
    Timer(5, greengrass_long_run).start()

# Execute the function above
greengrass_long_run()

# This is a dummy handler and will not be invoked
# Instead the code above will be executed in an infinite loop for our example
def function_handler(event, context):
    return