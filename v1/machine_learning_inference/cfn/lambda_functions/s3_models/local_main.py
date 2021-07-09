from threading import Timer

import os
import sys

from data_source.static_images import image_source

# import image_acquisition
# import load_model
import logging

log = logging.getLogger()
log.setLevel("INFO")

exists=(os.path.isfile("Inception-BN-symbol.json") and os.path.isfile("Inception-BN-0000.params") and os.path.isfile("synset.txt"))

def predict():
    model_path = './'
    source = image_source.ImageSource()
    global_model = load_model.ImagenetModel(model_path + 'synset.txt', model_path + 'Inception-BN')
    image = source.get_image()
    predictions = global_model.predict_from_image(image, N=1)

    predictions = global_model.predict_from_cam()
    log.info('predictions: {}'.format(predictions))
    result=map(lambda x: {'confidence':str(x[0]),'prediction':str(x[1])}, predictions)

    print(predictions)
    Timer(5, predict).start()

if not exists:
    import urllib.request
    urllib.request.urlretrieve ("http://data.mxnet.io/models/imagenet/inception-bn/Inception-BN-symbol.json", "Inception-BN-symbol.json")
    urllib.request.urlretrieve ("http://data.mxnet.io/models/imagenet/inception-bn/Inception-BN-0126.params", "Inception-BN-0000.params")
    urllib.request.urlretrieve ("http://data.mxnet.io/mxnet/models/imagenet/synset.txt", "synset.txt")
    log.info("Models downloaded")

predict()