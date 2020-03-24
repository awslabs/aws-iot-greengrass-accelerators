from dlr import DLRModel
import cv2

class DLRInference:

    #Loads a pre-trained model locally or from an external URL
    #and returns an MXNet graph that is ready for prediction
    def __init__(self, model_path, target='cpu'):

        # Load the NEO model with DLR runtime
        self.model = DLRModel(model_path, target)

    def predict(self, cvimage, reshape=(224, 224)):
        
        img = cv2.cvtColor(cvimage, cv2.COLOR_BGR2RGB)
        nn_input=cv2.resize(img, reshape)

        # The format of the output can be represented as [class_index, confidence_score, xmin, ymin, xmax, ymax]
        outputs = self.model.run({'data': nn_input})

        objects=outputs[0][0]
        scores=outputs[1][0]
        bounding_boxes=outputs[2][0]

        return objects, scores, bounding_boxes
    
