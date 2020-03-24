#
# Copyright 2010-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

# greengrass_long_run.py
# Demonstrates a simple machine learning inference
# using DLR model
#

import logging
import greengrasssdk
from threading import Timer
import time
import sys
import os
import json
import cv2
from data_source.static_images import image_source

from inference_runtime.dlr import load_model
import numpy as np

source_image_width = 224
source_image_height = 224

inference_image_width = 512
inference_image_height = 512

# Initialize the data source
source = image_source.ImageSource()
# source = image_source.GStreamImageSource(source_image_width,source_image_height)

log = logging.getLogger()

# Initialize the inference runtime with the model
AWS_GG_RESOURCE_PREFIX = os.environ['AWS_GG_RESOURCE_PREFIX']

# for local
log.info("export AWS_GG_RESOURCE_PREFIX={}".format(AWS_GG_RESOURCE_PREFIX))

model_path = AWS_GG_RESOURCE_PREFIX + "/dlr_model/"
global_model = load_model.DLRInference(model_path, 'cpu')

class_names = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 
                     'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 
                     'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']

# Creating a greengrass core sdk client
client = greengrasssdk.client('iot-data')

thing_name = os.environ['THINGNAME']
prediction_topic = "mli/predictions/{}".format(thing_name)

def greengrass_long_run():
    if global_model is not None:
        try:
            image, image_name = source.get_image()
            # cv2.imshow("appsink image arr", image)

            objects, scores, bounding_boxes = global_model.predict(image, reshape=(inference_image_width,inference_image_height))

            itemindex = np.where(scores>0.07)     
            confident_match=itemindex[0]                   
            for i in confident_match:                                   
                name = class_names[int(objects[i])]
                log.info("index:{}, class name:{}, scores:{}".format(i, name, scores[i]))

            thumbnail = cv2.resize(image, (200, 200))
            image_bytes = cv2.imencode('.jpg', thumbnail)[1].tostring()
            client.publish(topic=prediction_topic, payload=image_bytes)
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