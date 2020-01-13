import mxnet as mx
import numpy as np
import io
import cv2
import os
import urllib
import argparse
from collections import namedtuple
Batch = namedtuple('Batch', ['data'])

class ImagenetModel:

    #Loads a pre-trained model locally or from an external URL
    #and returns an MXNet graph that is ready for prediction
    def __init__(self, synset_path, network_prefix, params_url=None,
                 symbol_url=None, synset_url=None, context=mx.cpu(),
                 label_names=['prob_label'], input_shapes=[('data', (1, 3, 224, 224))]):

        # Download the symbol set and network if URLs are provided
        if params_url is not None:
            fetched_file = urllib.urlopen(params_url)
            with open(network_prefix + "-0000.params", 'wb') as output:
                output.write(fetched_file.read())

        if symbol_url is not None:
            fetched_file = urllib.urlopen(symbol_url)
            with open(network_prefix + "-symbol.json", 'wb') as output:
                output.write(fetched_file.read())

        if synset_url is not None:
            fetched_file = urllib.urlopen(synset_url)
            with open(synset_path, 'wb') as output:
                output.write(fetched_file.read())

        # Load the symbols for the networks
        with open(synset_path, 'r') as f:
            self.synsets = [l.rstrip() for l in f]

        # Load the network parameters from default epoch 0
        sym, arg_params, aux_params = mx.model.load_checkpoint(network_prefix, 0)

        # Load the network into an MXNet module and bind the corresponding parameters
        self.mod = mx.mod.Module(symbol=sym, context=context)
        self.mod.bind(for_training=False, data_shapes=input_shapes)
        self.mod.set_params(arg_params, aux_params)
        self.camera = None

    def predict(self, cvimage, reshape=(224, 224), N=5):
        topN = []

        # Switch RGB to BGR format (which ImageNet networks take)
        img = cv2.cvtColor(cvimage, cv2.COLOR_BGR2RGB)
        if img is None:
            return topN

        # Resize image to fit network input
        img = cv2.resize(img, reshape)
        img = np.swapaxes(img, 0, 2)
        img = np.swapaxes(img, 1, 2)
        img = img[np.newaxis, :]

        # Run forward on the image
        self.mod.forward(Batch([mx.nd.array(img)]))
        prob = self.mod.get_outputs()[0].asnumpy()
        prob = np.squeeze(prob)

        # Extract the top N predictions from the softmax output
        a = np.argsort(prob)[::-1]
        for i in a[0:N]:
            topN.append((prob[i], self.synsets[i]))
        return topN

    
