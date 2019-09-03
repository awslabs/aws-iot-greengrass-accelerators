# Machine Learning Inference

This Greengrass accelerator demonstrates how to run *machine learning inference* (MLI) on a local device at the edge, and publish the inference results to the connected Greengrass Aware Devices (GGAD), back to the cloud. 

This accelerator covers the following
1. Discuss various options for source of local inference
1. Local functions that invoke the inference services running on the device 

Example use cases for local MLI:

1. **Image Analytics in Surveillance** - Instead of having a security camera stream the content of its video to the cloud to be analyzed for certain situations such as unknown people or objects detection, the analysis can be done locally in the camera, and keeping the cloud-based analysis to a much smaller segment of the video data. Such architecture reduces the network congestion and sometimes costs with smaller amount of data to be sent to the cloud, and avoid any potential latencies which are very crucial in real-time surveillance application.
2. **Sensors Analytics** - Sensors attached to a machine can measure vibration, temperature, or noise levels, and inference at the edge can predice the state of the equipment and potential anomalies for early indications of failure. 

## MLI Accelerator Use Case

Imagine in an automated sorting and recycling facility center, there are numbers of camera that identify the wastes.

Each camera snaps the image of waste at predetermined frequency of 1 seconds. 

The local process will capture the image at predetermined frequency of 1 seconds, and forward the image to the local inference.

Finally, the process run the local logics based on the predictions.

The design is composed of three main parts:

* The source - the data source, such as a camera connected locally, or from a network streaming protocol such as RTSP.
* Greengrass Core - Local hardware that can connect to the camera and has a connection to the AWS Cloud.
* AWS Cloud - For model training, and feedback to improve model accuracy

## Overall Machine Learning Inference Process Flow

![MLI Solution Diagram](assets/greengrass-mli_overview.png)

The  processing flow of the accelerator is:

1. **Data acquisition** - This function acquire the raw data inputs from the source, such as data from the sensors, or images from the image capture devices.
1. **Data preprocessor** - This function will pre-process the data, such as resize of the image, or normalize the sensors data. The process will then forward the data to the local inference for predictions.
1. Inference engine can either running in Greengrass Connector, or in-process with the Lambda process. 
   * **Greengrass Connector** - If the algorithm is supported, Greengrass Connector can be used to infer using the model from the Amazon SageMaker. Lambda processes interface with the Greengrass Connectors using library [`greengrass-ml-sdk`](https://docs.aws.amazon.com/greengrass/latest/developerguide/what-is-gg.html#gg-ml-sdk-download)
   * **In-process** - If the model is compiled with Amazon SageMaker NEO compiler, the model can be loaded using NEO Deep Learning Runtime (NEO-DLR). Otherwise, the model can be loaded using respective runtimes, such as MXNet, TensorFlow or Chainer runtime.
4. For the in-process inference, the model can be accessed as local Greengrass Machine Learning Resource.
5. Model sources for the Greengrass are either models uploaded in S3 buckets, or save as Amazon SageMaker training jobs.
   * **Models in S3 buckets** - Amazon SageMaker Neo compiled models, or pre-trained models such as Inception-BN from the [model zoo](https://modelzoo.co/), can be upload to a S3 buckets and configure as Greengrass Machine Learning Resources
   * **Amazon SageMaker Training Jobs** - Greengrass supports models that are saved as Amazon SageMaker training jobs.
6. From the result of the inference, the Lambda function can handle the prediction accordingly locally. For example, to trigger an actuator based on the prediction result.

## Decision Tree Of Inference Runtime

The diagram below summarize the decision tree to which Greengrass Machine Learning Runtime can be used:

```plantuml
@startuml
!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v3.0/dist
!includeurl AWSPuml/AWSCommon.puml
!includeurl AWSPuml/InternetOfThings/all.puml

skinparam activity {
  FontName Aapex
}
skinparam wrapWidth 100
start
:Perform Machine Learning Inference at the edge on AWS IoT Greengrass Core v1.6 or later;
if (Uses Amazon SageMaker tools?) then (yes)
  if(Algorithm available in Greengrass connectors?) then (yes)
    :Use one of the connectors, such as **//Greengrass Image Classification connector//** or **//Greengrass Object Detection connector//**;
  elseif (Model trained in SageMaker and optimize with NEO?) then (yes)
    :Use **//NEO-AI runtime//** to run the model compiled by AWS SageMaker Neo in the Greengrass Group;
  else (no)
    :Deploy **//Amazon SageMaker//** model as the machine learning resource in the Greengrass Group with MXNet, TensorFlow or Chainer runtimes;
  endif
else (no)
  :Upload the pre-trained model in S3 and configure the model as machine learning resource in the Greengrass Group;
endif
stop
@enduml
```

### Algorithm available as Greengrass connectors
If the algorithm is available as Greengrass connectors, such as Image Classification, run the model using the Greengrass connector

### Trained in AWS SageMaker and compiled with AWS SageMaker Neo compiler
If the model is compiled with AWS SageMaker Neo, the model can be deployed in NEO-AI runtime.

### Trained in AWS SageMaker using MXNet, TensorFlow or Chainer
These models can be deployed as Machine Learning resources to the Greengrass Group with MXNet/TensorFlow/Chainer runtime.

### Models trained outside of AWS SageMaker
These models can uploaded in S3, and deployed as Machine Learning resources to the Greengrass Group

## Folder Structure

```text
machine_learning_inference/
├── README.md                             <-- This file!
├── S3_MODELS.md                           
├── cfn
│   ├── greengrass_mli-s3_models.cfn.yaml
│   └── lambda_functions
│       ├── s3_models
│       └── cfn_custom_resources
└── assets
```

The `cfn/` directory contains the CloudFormation assets to create the Greengrass configuration.

The `cfn/lambda_functions` directory contains the Lambda functions including the long-lived Lambda functions that runs in the Greengrass Core to run the inference. 

For example, the `cfn/lambda_functions/s3_models/` folder contains the Lambda functions that runs the local inference with pre-trained S3 models.

## Running machine learning inference on Greengrass

Details of how to run the machine learning inference is in separate document:

* [Machine Learning Inference using pre-trained model uploaded to S3](file://S3_MODELS.md)

