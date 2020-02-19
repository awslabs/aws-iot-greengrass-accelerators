import logging
import sys
import json
import os
import numpy as np
import greengrasssdk
import greengrass_machine_learning_sdk as ml
from threading import Timer
from data_source.static_images import image_source

CATEGORIES = ['ak47', 'american-flag', 'backpack', 'baseball-bat', 'baseball-glove', 'basketball-hoop', 'bat', 'bathtub', 'bear', 'beer-mug', 'billiards', 'binoculars', 'birdbath', 'blimp', 'bonsai-101', 'boom-box', 'bowling-ball', 'bowling-pin', 'boxing-glove', 'brain-101', 'breadmaker', 'buddha-101', 'bulldozer', 'butterfly', 'cactus', 'cake', 'calculator', 'camel', 'cannon', 'canoe', 'car-tire', 'cartman', 'cd', 'centipede', 'cereal-box', 'chandelier-101', 'chess-board', 'chimp', 'chopsticks', 'cockroach', 'coffee-mug', 'coffin', 'coin', 'comet', 'computer-keyboard', 'computer-monitor', 'computer-mouse', 'conch', 'cormorant', 'covered-wagon', 'cowboy-hat', 'crab-101', 'desk-globe', 'diamond-ring', 'dice', 'dog', 'dolphin-101', 'doorknob', 'drinking-straw', 'duck', 'dumb-bell', 'eiffel-tower', 'electric-guitar-101', 'elephant-101', 'elk', 'ewer-101', 'eyeglasses', 'fern', 'fighter-jet', 'fire-extinguisher', 'fire-hydrant', 'fire-truck', 'fireworks', 'flashlight', 'floppy-disk', 'football-helmet', 'french-horn', 'fried-egg', 'frisbee', 'frog', 'frying-pan', 'galaxy', 'gas-pump', 'giraffe', 'goat', 'golden-gate-bridge', 'goldfish', 'golf-ball', 'goose', 'gorilla', 'grand-piano-101', 'grapes', 'grasshopper', 'guitar-pick', 'hamburger', 'hammock', 'harmonica', 'harp', 'harpsichord', 'hawksbill-101', 'head-phones', 'helicopter-101', 'hibiscus', 'homer-simpson', 'horse', 'horseshoe-crab', 'hot-air-balloon', 'hot-dog', 'hot-tub', 'hourglass', 'house-fly', 'human-skeleton', 'hummingbird', 'ibis-101', 'ice-cream-cone', 'iguana', 'ipod', 'iris', 'jesus-christ', 'joy-stick', 'kangaroo-101', 'kayak', 'ketch-101', 'killer-whale', 'knife', 'ladder', 'laptop-101', 'lathe', 'leopards-101', 'license-plate', 'lightbulb', 'light-house', 'lightning', 'llama-101', 'mailbox', 'mandolin', 'mars', 'mattress', 'megaphone', 'menorah-101', 'microscope', 'microwave', 'minaret', 'minotaur', 'motorbikes-101', 'mountain-bike', 'mushroom', 'mussels', 'necktie', 'octopus', 'ostrich', 'owl', 'palm-pilot', 'palm-tree', 'paperclip', 'paper-shredder', 'pci-card', 'penguin', 'people', 'pez-dispenser', 'photocopier', 'picnic-table', 'playing-card', 'porcupine', 'pram', 'praying-mantis', 'pyramid', 'raccoon', 'radio-telescope', 'rainbow', 'refrigerator', 'revolver-101', 'rifle', 'rotary-phone', 'roulette-wheel', 'saddle', 'saturn', 'school-bus', 'scorpion-101', 'screwdriver', 'segway', 'self-propelled-lawn-mower', 'sextant', 'sheet-music', 'skateboard', 'skunk', 'skyscraper', 'smokestack', 'snail', 'snake', 'sneaker', 'snowmobile', 'soccer-ball', 'socks', 'soda-can', 'spaghetti', 'speed-boat', 'spider', 'spoon', 'stained-glass', 'starfish-101', 'steering-wheel', 'stirrups', 'sunflower-101', 'superman', 'sushi', 'swan', 'swiss-army-knife', 'sword', 'syringe', 'tambourine', 'teapot', 'teddy-bear', 'teepee', 'telephone-box', 'tennis-ball', 'tennis-court', 'tennis-racket', 'theodolite', 'toaster', 'tomato', 'tombstone', 'top-hat', 'touring-bike', 'tower-pisa', 'traffic-light', 'treadmill', 'triceratops', 'tricycle', 'trilobite-101', 'tripod', 't-shirt', 'tuning-fork', 'tweezer', 'umbrella-101', 'unicorn', 'vcr', 'video-projector', 'washing-machine', 'watch-101', 'waterfall', 'watermelon', 'welding-mask', 'wheelbarrow', 'windmill', 'wine-bottle', 'xylophone', 'yarmulke', 'yo-yo', 'zebra', 'airplanes-101', 'car-side-101', 'faces-easy-101', 'greyhound', 'tennis-shoes', 'toad', 'clutter']

source = image_source.ImageSource()
client = greengrasssdk.client('iot-data')
inference_mlclient = ml.client('inference')
feedback_mlclient = ml.client('feedback')

log = logging.getLogger()
thing_name = os.environ['THINGNAME']
prediction_topic = "mli/predictions/{}".format(thing_name)
feedback_config_id = "RandomSamplingConfiguration"

def invoke_feedback_connector(content,model_prediction):
    log.info("Invoking feedback connector.")
    try:
        feedback_mlclient.publish(
            ConfigId=feedback_config_id,
            ModelInput=content,
            ModelPrediction=model_prediction
        )
    except Exception as e:
        logging.info("Exception raised when invoking feedback connector:{}".format(e))

def greengrass_long_run():
    log.debug('invoking Greengrass ML Inference using GG Connector')

    try:
        content = source.get_image()        

        resp = inference_mlclient.invoke_inference_service(
            AlgoType='image-classification',
            ServiceName='image-classification',
            ContentType='image/jpeg',
            Body=content
        )

        predictions = resp['Body'].read()
        log.debug('predictions: {}'.format(predictions))

        # The connector output is in the format: [0.3,0.1,0.04,...]
        # Remove the '[' and ']' at the beginning and end.
        predictions = predictions[1:-1]
        predictions_arr = np.fromstring(predictions, dtype=np.float, sep=',')
        log.debug('predictions_arr: {}'.format(predictions_arr))

        prediction_confidence = predictions_arr.max()
        predicted_category = CATEGORIES[predictions_arr.argmax()]
        log.info('predicted_category: {}, confidence: {}'.format(predicted_category, prediction_confidence))

        # predictions = global_model.predict_from_cam()
        result={}
        result["confidence"]=prediction_confidence
        result["prediction"]=predicted_category
        client.publish(topic=prediction_topic, payload=json.dumps(result))

        # Perform business logic that relies on the predictions_arr, which is an array
        # of probabilities.

        # Uses ML Connector to call the Feedback connector directly
        # invoke_feedback_connector(content,result)

    except ml.GreengrassInferenceException as e:
        logging.exception('inference exception {}("{}")'.format(e.__class__.__name__, e))
    except ml.GreengrassDependencyException as e:
        logging.exception('dependency exception {}("{}")'.format(e.__class__.__name__, e))
    except Exception as e:
        logging.fatal(e, exc_info=True)
    # Schedule the infer() function to run again in one second.
    Timer(1, greengrass_long_run).start()

greengrass_long_run()

def handler(event, context):
    return
