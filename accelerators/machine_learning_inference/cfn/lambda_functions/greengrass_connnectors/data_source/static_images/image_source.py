#
# Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import logging
import sys
import cv2
import os
import glob
from functools import reduce

class ImageSource():
    def __init__(self):
        self.log = logging.getLogger()
        module_path = os.path.abspath(os.path.dirname(__file__))
        self.images = reduce(lambda all,image: all + glob.glob(module_path + "/images/" + image), ['*.png', '*.jpg'], list())
        self.image_index = 0

    def get_image(self):
        try:
            self.image_index = (self.image_index + 1 ) % len(self.images)
            image_name = self.images[self.image_index]
            self.log.info('image name: {}'.format(image_name))
            with open(image_name, 'rb') as f:
                content = bytearray(f.read())
            # image = cv2.imread(image_name)
                return content
        except:
            e = sys.exc_info()[0]
            self.log.exception("Exception occured during prediction: {}".format(e))
