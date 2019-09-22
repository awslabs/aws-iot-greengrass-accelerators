# Greengrass Machine Learning Python SDK
The Greengrass Machine Learning SDK provides an interface to send inference requests and receive results.

## invoke_inference_service(**kwargs)

After deploying a Greengrass Machine Learning connector to a Greengrass core, a client lambda uses this API to get inferences from the model at the service name you specified while adding the connector to your Greengrass group.

### Request Syntax
```python
import greengrass_machine_learning_sdk
client = greengrass_machine_learning_sdk.client('inference')
response = client.invoke_inference_service(
    AlgoType='string',
    ServiceName='string',
    ContentType='string',
    Accept='string',
    Body=b'bytes'|file
)
```

#### Parameters
* **AlgoType** (string): *[Required]* The name of the inference algorithm type. You can find the value to be passed in on Greengrass Machine Learning online documentation.
* **ServiceName** (string): *[Required]* The name of the local inference service when the connector was added to your Greengrass group.
* **Body** (bytes or seekable file-like object): *[Required]* Provides input data, in the format specified in the **ContentType** request header. All of the data in the body will be passed to the model.
* **ContentType** (string): *[Required]* The MIME type of the input dat in the **Body** field.
* **Accept** (string): *[Optional]* The desired MIME type of the inference in the response.

### Response type
dict

### Response Syntax
```python
{
    'Body': StreamingBody(),
    'ContentType': 'string'
}
```

#### Response Structure
* **Body** (StreamingBody): Includes the inference result provided by the model.
* **ContentType** (string): The MIME type of the inference result returned in the **Body** field.

## publish(**kwargs)

After deploying a Greengrass ML Feedback connector to a Greengrass core, a client lambda can use this API to publish input to a model and the resulting prediction. Model input such as image, json, or sound, will be uploaded to the S3 location configured in the ML Feedback connector where it can be used to retrain a model. Model predictions are published to the feedback/message/prediction where they can be analyzed.

See connector documentation for more details.

### Request Syntax
```python
import greengrass_machine_learning_sdk
client = greengrass_machine_learning_sdk.client('feedback')
client.publish(
	ConfigId='string',
	ModelInput='bytes',
	ModelPrediction='list',
	Metadata='dict'
)
```

#### Parameters
* **ConfigId** (string): *[Required]* ConfigId matching a specific configuration defined in the ML Feedback connector configuration.
* **ModelInput** (bytes): *[Required]* Data that was passed to a model for inference.
* **ModelPrediction** (list): *[Required]* Representation of the model's output as a list of probabilities (float). Ex: [0.25, 0.60, 0.15].
* **Metadata** (dict): *[Optional]* Additional metadata to attach to the uploaded S3 sample as well as messages published to the /feedback/message/prediction topic.

### Response type
None

### Response Syntax
None

#### Response Structure
None