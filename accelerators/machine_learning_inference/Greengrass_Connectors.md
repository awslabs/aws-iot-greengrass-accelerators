# Greengrass Machine Learning Inference (MLI) using Greengrass Connectors 

This document describe the steps in setting up Greengrass Machine Learning Inference, using Greengrass Image Classification Connector with Amazon SageMaker training job. Greengrass ML Feedback connector will be used to collect data from the field for future model retraining or prediction results analysis.

## Greengrass Machine Learning (ML) Connectors

Using Greengrass Connectors for Machine Learning at the edge offers the following advantages: 

1. Greengrass ML Connectors are prebuilt modules to help accelerate the development lifecycle for ML at the edge. Deployment of Greengrass ML Connectors includes the libraries optimized for the hardware platform, eliminates the complexity of having to manage the libraries for dfferent hardware platform which is required if [running the ML without any Greengrass Connector](https://github.com/awslabs/aws-iot-greengrass-accelerators/blob/master/accelerators/machine_learning_inference/S3_MODELS.md#how-to-deploy-the-accelerator)
2. Greengrass ML Feedback Connector supports [sampling strategies](https://docs.aws.amazon.com/en_pv/greengrass/latest/developerguide/ml-feedback-connector), offering cost effectiveness in collecting data in the field. 

## Design Pattern

![MLI Greengrass Connectors Solution Diagram](assets/mli-connectors.png)

The common design patterns of using Greengrass Connectors:

1. Creates a Amazon SageMaker training job to create the model. When the Greengrass configuration is being deployed, the Greengrass Core will download the model from the *Amazon SageMaker* training job as a local machine learning resource.
2. **Data acquisition** - This function periodically acquire the raw data inputs from a image source. In this example, we are using static images to simulate image sources.
3. **Data preprocessor** - This function pre-process the image by resize to the images used to train the model.
4. **Estimator** - This function predict the data input with the connector via IPC
5. **Greengrass ML Image Classification Connector** - The Connector loads the model from local Greengrass resource and invoke the model. 
6. The process will handle the prediction result, with object detected and confidence level.
7. The result can be used to trigger an action, or send it back to the cloud for further processing.
8. **Greengrass ML Feedback Connector** - Greengrass ML Feedback Connector sends field data back to AWS according to the sampling strategy configured
9. Greengrass ML Feedback Connector sends unlabeled data to AWS
10. Unlabled data can be labeled using Amazon Ground Truth, and the labeled data can be used to retrain the model
11. Greengrass ML Feedback Connector sends prediction performance which can be used for performance analysis in realtime using AWS services.

## How to Deploy the Accelerator

To launch this accelerator, there are a few prerequisites and steps to complete. It is assumed you have basic experience with AWS IoT via the console and CLI.

The main steps for deployment are:
1. _Complete prerequisites._ Ensure there is an AWS IoT certificate and private key created and accessible locally for use.
2. _Create the Amazon SageMaker training job._ We will use an example notebook from Amazon SageMaker to create the model with a Amazon SageMaker training job.
3. _Generate and launch the CloudFormation stack._ This will create the Lambda functions, the Greengrass resources, and an AWS IoT thing to be used as the Greengrass Core. The certificate will be associated with the newly created Thing. At the end, a Greengrass deployment will be created and ready to be pushed to the Greengrass core hardware.
4. _Create the config.json file_, using the outputs from the CloudFormation. Then place all files into the `/greengrass/certs` and `/greengrass/config` directories.
5. _Deploy to Greengrass_. From the AWS Console, perform a Greengrass deployment that will push
all resources to the Greengrass Core and start the MLI operations.

### Verify Prerequisites

The following is a list of prerequisites to deploy the accelerator:

* AWS Cloud
  * Ensure you have an AWS user account with permissions to manage `iot`, `greengrass`, `lambda`, `cloudwatch`, and other services during the deployment of the CloudFormation stack.
  * Create an AWS IoT Certificate and ensure it is activated and the certificate and private key files are saved locally. This certificate will be associated with an AWS IoT *thing* created by the CloudFormation stack. Copy the certificates *Certificate ARN*, which will be used as a parameter for the CloudFormation stack. The *Certificate ARN* will look similar to this: `arn:aws:iot:REGION:ACCOUNTNAME:cert/27b42xxxxxxx120017a`, and the *Certificate ID* is the trailing alphanumerics, such as `27b42xxxxxxx120017a`
    * You can use this AWS CLI command to create new certificate. The output value from the CLI, *Certificate ID* will be needed to create the CloudFormation stack. 
     ```bash
     aws iot create-keys-and-certificate --certificate-pem-outfile "mli.cert.pem" --public-key-outfile "mli.public.key" --private-key-outfile "mli.private.key" --set-as-active --query certificateId --output text
     ``` 
  * *In the same region where CloudFormation resources will be created*, create S3 bucket to hold the packaged files. Please see [this link](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-cli-package.html) for more details. This bucket needs to have read and write access by the IAM role that is running the CloudFormation `package` and `deploy`.
  * Create a S3 bucket to hold the feedback data from the Greengrass Feedback Connector.

* Local Environment (where running the accelerator)
  * From the certificate creation step above, note the location of the X.509 certificate and private key registered and activated with AWS IoT.
  * Ensure a recent version of the AWS CLI is installed and a user profile with permissions mentioned above is available for use.

* Greengrass Core
     * **AWS IoT Greengrass Core SDK Software** which can be installed using pip command `sudo pip3.7 install greengrasssdk`
     * **OpenCV** for Python3.7
  * Steps on running Greengrass on EC2 can be found in [AWS Greengrass Core on AWS EC2](#AWS-Greengrass-Core-on-AWS-EC2)

### Amazon SageMaker training job

Amazon SageMaker Notebook Instances contains example notebook (also available from https://github.com/awslabs/amazon-sagemaker-examples). 

In this Greengrass Connector accelerator, we will be using the notebook that uses Caltech ImageNet for Image Classification (https://github.com/awslabs/amazon-sagemaker-examples/tree/master/sagemaker_neo_compilation_jobs/imageclassification_caltech)

1. Login to Amazon SageMaker Notebook Instances console https://console.aws.amazon.com/sagemaker/home?#/notebook-instances
2. Select `Create notebook instance`
3. Enter a name in `Notebook instance name`, such as `greengrass-connector-training`
4. Use the default `ml.t2.medium` instance type
5. Leave all default options and select `Create notebook instance`
6. Wait for the instance status to be `InService`, and select `Open Jupyter`
7. Select `SageMaker Example` tab, expand `Sagemaker Neo Compilation Jobs`, `Image-classification-fulltraining-highlevel-neo.ipynb`, select `Use`
8. Keep default option for the file name and select `Create copy`
9. We need to update the hyper-parameter of the sample notebook with `use_pretrained_model=1`, otherwise the training will requires larger epochs for better accuracy
10. Locate the cell that configure the `hyper-parameters` and add the additional `use_pretrained_model=1`
```
ic.set_hyperparameters(num_layers=18,
[...]
                       precision_dtype='float32',
                       use_pretrained_model=1)
```
11. Let's make sure the training job is easily identifiable, by using a `base_job_name` in the `sagemaker.estimator`. **You will need this name prefix when creating the stack**
12. Locate the cell that initialize the `sagemaker.estimator` and add the `base_job_name`, for example, using `greengrass-connector` as the prefix:
```
ic = sagemaker.estimator.Estimator(training_image,
                                   role, 
[...]                                         
                                   sagemaker_session=sess,
                                   base_job_name= 'greengrass-connector')
```
14. Add a cell below the cell that do the training `ic.fit()` and the command `ic.latest_training_job.name` in the empty cell. This will give us the name of the training job we need for the Greengrass Connector
15. Select the `Cell` from thet notebook menu and `Run All`

[Sample notebook Image-classification-fulltraining.ipynb](notebooks/Image-classification-fulltraining.ipynb) with all these changes is in the `notebooks/` folder.

### Launch the CloudFormation Stack

Prior to launching the accelerator locally, a CloudFormation package needs to be created, and then the CloudFormation stack launched from the Template. Follow the steps below to create the package via the command line, and then launch the stack via the CLI or AWS Console.

The CloudFormation template does most of the heavy lifting. Prior to running, each *input* template needs to be processed to an *output* template that is actually used. The package process uploads the Lambda functions to the S3 bucket and creates the output template with unique references to the uploaded assets. 

To create or overwrite the templates, perform the following steps from a command line or terminal session:

1. Clone the repository `git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git` and change to `aws-iot-greengrass-accelerators/accelerators/machine_learning_inference`, where this `Greengrass_Connectors.MD` file is located.

1. Create the CloudFormation output file using the AWS CLI.  Using the commands below, you can either preset the \$AWS_PROFILE, \$REGION, \$CFN_S3_BUCKET, \$ML_FEEDBACK_S3_BUCKET_NAME, \$TRAININGJOBNAME_CONTAINS,\$THINGNAME and \$CERTIFICATE_ID variables, or reference those directly via the `aws cloudformation package` command. The result of that command will be an *OUTPUT* CloudFormation template file, along with the packaged Lambda functions being copied to the S3 bucket. The `AWS_PROFILE` contains the credentials, account details, and optionally region to create the CloudFormation stack.

   Complete list of commands to create the CloudFormation template file, upload assets, and create a stack (note the changes for the `--parameter-overrides` section).
   
   ```bash
   # BASH commands (replace exports with your AWSCLI profile, region, and S3 bucket settings)
   # AWS_PROFILE contains permissions to fully create and launch the CloudFormation package and template
   export AWS_PROFILE=<your-profile-here>
   export AWS_REGION=<your-region>
   export STACK_NAME=<Cloudformation stack name>
   export CFN_S3_BUCKET=<your_s3_bucket_that_holds_cloudformation>         # Needs to be located in same region as where the CloudFormation stack is created.
   export FEEDBACK_S3BUCKET_NAME=<s3 bucket name for the model feedback> 
   export CORENAME=<Thing name of the device to be the GreenGrass Core>
   export CERTIFICATE_ID=<Certificate ID>
   export TRAININGJOBNAME_CONTAINS=<base_job_name used in the SageMaker training job, such as "greengrass-connector">
                                                
   # Clean up any previously created files
   rm *-OUTPUT.yaml
   aws cloudformation package \
   --template-file cfn/mli_accelerator-connector-INPUT.cfn.yaml \
   --output-template-file mli_accelerator-connector-OUTPUT.yaml \
   --s3-bucket ${CFN_S3_BUCKET} --profile ${AWS_PROFILE} --region ${AWS_REGION}
     
   # If using the AWS Console, upload the mli_accelerator_s3_models-OUTPUT.yaml and continue with the parameters.
   # Below are the steps to deploy via the command line.
     
   # To deploy back-end stack from CLI (change --stack-name and --parameter-overrides to expected values)
   aws cloudformation deploy \
     --profile ${AWS_PROFILE} \
     --region ${AWS_REGION} \
     --stack-name ${STACK_NAME} \
     --template mli_accelerator-connector-OUTPUT.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
       CoreName=${CORENAME} \
       CertIdParam=${CERTIFICATE_ID} \
       TrainingJobNameContains=${TRAININGJOBNAME_CONTAINS} \
       FeedbackS3BucketName=${FEEDBACK_S3BUCKET_NAME}
   ```

At this point, all resources have been created and an initial Greengrass deployment has also been created and ready to be sent to the device.

### Configure and Starts the Greengrass Core

With the stack deployed, we use one output from the CloudFormation stack, the *GreengrassConfig* value, along with the certificate and private key to complete the `config.json` so that Greengrass Core can connect and authenticate.

1. In the local computer, create a temporary folder, such as `greengrass/`.
1. Make 2 folders in the temporary folder, `certs/` and `config/`.
1. Change into `certs` folder
   1. Download to `certs` directory the [Amazon Root CA1](https://www.amazontrust.com/repository/AmazonRootCA1.pem) root certificate authority file used to verify the AWS IoT and AWS Greengrass endpoints. If the link opens with the contents in your browser, use alt-click and *Save As…* instead and save as `certs/AmazonRootCA1.pem`.
   1. Copy the certificate and private key files into the `certs/` folder
1. Change into `config/` folder 
   1. Retrieve the `config.json` created from the CloudFormation, using the AWS CLI command
   ```bash
   aws cloudformation describe-stacks \
   --stack-name greengrass-mli-accelerator \
   --output text \  
   --query 'Stacks[*].Outputs[?OutputKey==`GreengrassConfig`].OutputValue' 
   ```
   or you can pipe through a Python json tool for pretty print:
   ```bash
   aws cloudformation describe-stacks \
   --stack-name greengrass-mli-accelerator \
   --output text \  
   --query 'Stacks[*].Outputs[?OutputKey==`GreengrassConfig`].OutputValue' 
   | python -m json.tool 
   ```
   1. Paste the output to file `config.json` in the `config/` folder
   1. Open `config.json` file and replace *CERTIFICATE_NAME_HERE* with the file name and extension of your certificate (e.g., `123beef-certificate.pem.crt`).
   1. Do the same replacing *PRIVATE_KEY_FILENAME_HERE* with the name of your private key (e.g., `123beef-private.pem.key`).
   1. Save the file.
1. Change into the temporary folder, the parent folder of both `certs/` and `config/`
1. Compress both `certs/` and `config/` into a single file, such as `zip -r greengrass-setup.zip certs/* config/*`
1. Copy the `greengrass-setup.zip` to the Greengrass Core machine, such as using command `scp`
1. Remote access to the Greengrass Core machine, such as using command `ssh`
1. Go to the folder where Greengrass was installed, such as `/greengrass`
1. Unzip the contents from the 2 folders in `greengrass-setup.zip` into `certs/` and `config/` folders respectively, using the command `sudo unzip -o greengrass-setup.zip -d /greengrass`
1. Verify that all certificates are in the `certs/` folder, and `config.json` is in the `config/` folder.
1. Restart the Greengrass software, such as using the command `sudo /greengrass/ggc/core/greengrassd restart`, or `sudo systemctl restart greengrass` if Greengrass Core is under `systemctl` management.
1. Monitor the log file of the Greengrass software to make sure that Greengrass software started properly, such as using the command `tail -F /greengrass/ggc/var/log/system/runtime.log`.
1. If the Greengrass software started properly, you should see these in the log file
   ```log
   [2019-08-18T01:14:55.69-07:00][INFO]-===========================================
   [2019-08-18T01:14:55.69-07:00][INFO]-Greengrass Version: 1.9.2-RC4
   [2019-08-18T01:14:55.69-07:00][INFO]-Greengrass Root: /greengrass
   [2019-08-18T01:14:55.69-07:00][INFO]-Greengrass Write Directory: /greengrass/ggc
   [2019-08-18T01:14:55.69-07:00][INFO]-Group File Directory: /greengrass/ggc/deployment/group
   [...]
   [2019-08-18T01:14:56.739-07:00][INFO]-All topics subscribed.    {"clientId": "<THING NAME>"}
   ```
1. From the Greengrass Console, navigate to your created Greengrass Group and perform *Actions->Deploy* to deploy to the Greengrass Core machine.
   1. Alternatively, Greengrass deployment command can be found in from the CloudFormation stack, using the command below:

   ```bash
   aws cloudformation describe-stacks \
   --stack-name ${STACK_NAME} \
   --output text \
   --query 'Stacks[*].Outputs[?OutputKey==`CommandToDeployGroup`].OutputValue' 
   ```
   The output will be the command that you can copy and run to deploy to the Greengrass core, for example, 

   ```bash
   aws --region <AWS Region> greengrass create-deployment --group-id <Greengrass Group ID> --deployment-type NewDeployment --group-version-id $(cut -d'/' -f6 <<< arn:aws:greengrass:<AWS Region>:<AWS Account ID>:/greengrass/groups/<Greengrass Group ID>/versions/<Greengrass Group Version ID> )
   ```

### AWS Greengrass Core on AWS EC2

To test out this accelererator without any hardware, you can install the Greengrass on an EC2 to simulate as a Greengrass Core

1. Create a EC2 running Greengrass, using the Cloudformation template in `cfn/greengrass_core_on_ec2-s3_models.cfn.yml`
1. Once the instance is created, copy the `greengrass-setup.zip` to the EC2
1. In the EC2, extract `greengrass-setup.zip` into `/greengrass` folder using command `sudo unzip -o greengrass-setup.zip -d /greengrass`
1. Restart the Greengrass daemon using the command `sudo systemctl restart greengrass`

### Expected Output

#### Prediction

The predictions will be published from the Greengrass Core to the cloud, via topic `mli/predictions/<THING NAME>`. The message can be observed using the MQTT Test client in AWS IoT Console

1. Login to https://console.aws.amazon.com/iot/home?#/test
1. Change to the region where the Greengrass Core is connecting to
1. In the `Subscription topic`, enter either the specific topic for the Greengrass Core `mli/predictions/<THING NAME>` or generic topic `mli/predictions/#`
1. Select `Subscribe`
1. The prediction messages should be shown in the console, such as 
```
[
  {
    "confidence": "0.21719395",
    "prediction": "n03983396 pop bottle, soda bottle"
  }
]
```

#### Feedback

For the Greengrass Feedback Connector, we created 2 configurations, one for the confidence of prediction lower than 0.5, and one for the entropy:

```
{
  "LC50": {
    "s3-bucket-name": "kangrich-greengrass-us-west-2",
    "s3-prefix": "confidence-lower-than-50",
    "content-type": "image/jpeg,image/png",
    "sampling-strategy": {
      "strategy-name": "LEAST_CONFIDENCE",
      "threshold": 0.5
    }
  },
  "Entropy": {
    "s3-bucket-name": "kangrich-greengrass-us-west-2",
    "s3-prefix": "entropy",
    "content-type": "image/jpeg,image/png",
    "sampling-strategy": {
      "strategy-name": "ENTROPY",
      "threshold": 0
    }
  }
}
```

The configuration ID is then configured to the Greengrass Image Classification Connector as `MLFeedbackConnectorConfigId` and the Greengrass Image Classification Connector will invoke the ML Feedback Connector accordingly.

Alternatively, the Greengrass ML Feedback Connector can be invoked explicitly in the Lambda function, such as:

```python
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
```

## FAQ and Help

Good reference of common issues can be found in https://github.com/awsdocs/aws-greengrass-developer-guide/blob/master/doc_source/gg-troubleshooting.md

### Out-of-memory

If you noticed that `memUsed` is higher than the allocated memory `memSize` for either the connector or Lambda function, the function will not be started

```
[2019-08-28T21:29:03.757Z][WARN]-Worker consumed all allocated memory! Memory Usage (KB).	{"workerId": "e544111a-03f5-40da-5e5c-23df2f6ced65", "funcArn": "arn:aws:lambda:<AWS Region>:<AWS Account ID>:function:pinned-ggc-mli-stack:6", "memSize": 120000, "memUsed": 165172}
[2019-08-28T21:29:03.757Z][ERROR]-Worker is ungracefully killed.	{"workerId": "e544111a-03f5-40da-5e5c-23df2f6ced65", "funcArn": "arn:aws:lambda:<AWS Region>:<AWS Account ID>:function:pinned-ggc-mli-stack:6", "state": "signal: killed"}
```

### Resolution

Try increase the memory allocated for that function.
