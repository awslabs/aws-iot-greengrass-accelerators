#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import logging
import sys
import cv2
import picamera
import time
import io
import numpy as np

class ImageSource():

    #Loads a pre-trained model locally or from an external URL
    #and returns an MXNet graph that is ready for prediction
    def __init__(self):
        self.log = logging.getLogger()
        self.camera = None

    #Captures an image from the PiCamera, then sends it for prediction
    def get_image(self):
        try:
            if self.camera is None:
                self.camera = picamera.PiCamera()

            stream = io.BytesIO()
            self.camera.start_preview()
            time.sleep(2)
            self.camera.capture(stream, format='jpeg')
            # Construct a numpy array from the stream
            data = np.fromstring(stream.getvalue(), dtype=np.uint8)
            # "Decode" the image from the array, preserving colour
            image = cv2.imdecode(data, 1)
            return image, "picamera"
        except:
            e = sys.exc_info()[0]
            self.log.exception("Exception occured during acquisition: {}".format(e))
