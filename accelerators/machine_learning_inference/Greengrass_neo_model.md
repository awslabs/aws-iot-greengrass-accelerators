# Greengrass Machine Learning Inference (MLI) using pre-built Amazon SageMaker Neo Deep Learning Runtime (DLR)

This document describe the steps in setting up Greengrass Machine Learning Inference, using a classification model trained in Amazon SageMaker and compiled with Amazon SageMaker Neo compiler, and runs in the AWS IoT Greengrass pre-built Amazon SageMaker Neo Deep Learning Runtime (DLR).

## Greengrass Machine Learning (ML) Connectors

**Amazon SageMaker Neo** enables machine learning models to train once and run anywhere in the cloud and at the edge. Neo automatically optimizes TensorFlow, MXNet, PyTorch, ONNX, and XGBoost models for deployment on ARM, Intel, and Nvidia processors. Optimized models run up to twice as fast and consume less than a tenth of the memory footprint. Example notebook to compare the performance improvement between original model versus neo-optimized model can be found in [amazon-sagemaker-examples](https://github.com/awslabs/amazon-sagemaker-examples/blob/master/sagemaker_neo_compilation_jobs/mxnet_mnist/mxnet_mnist_neo.ipynb
)

Using Neo with AWS IoT Greengrass, you can retrain these models in Amazon SageMaker, and update the optimized models quickly to improve intelligence on these edge devices. You can use a broad range of devices based on the Nvidia Jetson TX2, Arm v7 (Raspberry Pi), or Intel Atom platforms. List of the supported target devices can be found in [Amazon SageMaker API Reference](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_OutputConfig.html)

## Design Pattern

![MLI Greengrass NEO DLR runtime Solution Diagram](assets/mli-neo_dlr.png)

The common design patterns of using Greengrass Connectors:

1. Use a Amazon SageMaker training job to train and compile the model. When the Greengrass configuration is being deployed, the Greengrass Core will download the model from the *S3 bucket* as configured in the Machine Learning Resources, to the local storage as a *Machine Learning Resource*
2. **Data acquisition** - This function periodically acquire the raw data inputs from a image source. In this example, we are using static images to simulate image sources.
3. **Data preprocessor** - This function pre-process the image by resize to the images used to train the model.
4. **Estimator** - This function predict the data input with the connector via IPC
5. **Estimator loads the NEO model** - The local Lambda script will load the NEO model with DLR runtime
6. The process will handle the prediction result, with object detected and confidence level.
7. The result can be used to trigger an action, or send it back to the cloud for further processing.

## How to Deploy the Accelerator

To launch this accelerator, there are a few prerequisites and steps to complete. It is assumed you have basic experience with AWS IoT via the console and CLI.

The main steps for deployment are:
1. _[Prerequisites.](#prerequisites)_ Ensure there is an AWS IoT certificate and private key created and accessible locally for use.
2. _[Train the ML model.](#train-the-model-with-amazon-sagemaker)_ We will use an example notebook from Amazon SageMaker to train the model with the Image Classification Algorithm provided by Amazon SageMaker.
3. _[Generate and launch the CloudFormation stack.](#launch-the-cloudformation-stack)_ This will create the Lambda functions, the Greengrass resources, and an AWS IoT thing to be used as the Greengrass Core. The certificate will be associated with the newly created Thing. At the end, a Greengrass deployment will be created and ready to be pushed to the Greengrass core hardware.
4. _[Create the config.json file](#configure-the-greengrass-core)_, using the outputs from the CloudFormation. Then place all files into the `/greengrass/certs` and `/greengrass/config` directories.
5. _[Deploy to Greengrass](#deploy-cloud-configurations-to-the-greengrass-core)_. From the AWS Console, perform a Greengrass deployment that will push all resources to the Greengrass Core and start the MLI operations.

### Prerequisites

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
     * On the [AWS IoT Greengrass Machine Learning Runtimes and Precompiled Libraries](https://docs.aws.amazon.com/greengrass/latest/developerguide/what-is-gg.html#gg-ml-runtimes-pc-libs) downloads page, locate the Deep Learning Runtime version 1.0.0 for your platform, and choose Download.
     * **AWS IoT Greengrass Core SDK Software** which can be installed using pip command `sudo pip3.7 install greengrasssdk`
     * **OpenCV** for Python3.7
  * Steps on running Greengrass on EC2 can be found in [AWS Greengrass Core on AWS EC2](#AWS-Greengrass-Core-on-AWS-EC2)

### Train the model with Amazon SageMaker

We will be using [the example notebook from Amazon SageMaker](https://github.com/awslabs/amazon-sagemaker-examples/ssd_gg/sagemaker_neo_compilation_jobs/gluoncv_ssd_mobilenet) to train the model using GluonCV SSD, and compile with NEO compiler.

1. Login to Amazon SageMaker Notebook Instances console https://console.aws.amazon.com/sagemaker/home?#/notebook-instances
2. Select `Create notebook instance`
3. Enter a name in `Notebook instance name`, such as `greengrass-ssd-dlr-model`
4. Use the default `ml.t2.medium` instance type
5. Leave all default options and select `Create notebook instance`
6. Wait for the instance status to be `InService`, and select `Open JupyterLab`
1. From the top menu, choose `File`, `New`, then `Terminal`
1. We will copy the example notebook and Python script from sample folder to our working folder. In the `terminal`, copy the whole directory to `~/SageMaker/`, using command `$  cp -R sample-notebooks/sagemaker_neo_compilation_jobs/gluoncv_ssd_mobilenet ~/SageMaker/`
1. From the left hand navigation, navigate to `gluoncv_ssd_mobilenet` and opens the Jupyter file `gluoncv_ssd_mobilenet_neo.ipynb`, and make sure the Gluon training Python script `ssd_entry_point.py` is in the same folder.
1. From the top menu, choose `Run`, then `Run All Cells`

#### Change the compile target

In cell **12** of `gluoncv_ssd_mobilenet`, the default DLR compile target is `ml_p3`. You will need to change the compiler to your hardware, such as

```
compiled_model = ssd_estimator.compile_model(target_instance_family='imx8qm', 
                                             input_shape={'data':[1, 3, 512, 512]},
                                             output_path=s3_output_location,
                                             framework='mxnet', 
                                             framework_version='1.4.1'
                                            )
```

#### Required parameter for next step

We need the S3 uri of the compiled model when creating the cloud configuration of the Greengrass Group, as the parameter `ML_S3_BUCKET_URI` of the Cloudformation stack. 

You can add a cell after cell **12** to print out the value of `compiled_model.model_data`, and you should see the value of the model such as `'s3://sagemaker-us-east-1-<AWS Account ID>/DEMO-ObjectDetection/output/model-imx8qm.tar.gz'`.

### Launch the CloudFormation Stack

Now that we have the NEO model compiled in `s3_output_location`, we will next create the cloud configuration of the Greengrass Group.

We will be using the [Cloudformation stack](cfn/mli_accelerator_dlr_models-INPUT.cfn.yaml). Follow the steps below to create the package via the command line, and then launch the stack via the CLI or AWS Console.

The CloudFormation template does most of the heavy lifting. Prior to running, each *input* template needs to be processed to an *output* template that is actually used. The package process uploads the Lambda functions to the S3 bucket and creates the output template with unique references to the uploaded assets. 

To create or overwrite the templates, perform the following steps from a command line or terminal session:

1. Clone the repository `git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git` and change to `aws-iot-greengrass-accelerators/accelerators/machine_learning_inference`, where this `Greengrass_neo_model.MD` file is located.

1. The Cloudformation stack [mli_accelerator-neo-INPUT.cfn.yaml](accelerators/machine_learning_inference/cfn/mli_accelerator-neo-INPUT.cfn.yaml) uses `AWS::Serverless` macros, therefore you will need to `package` before `deploy`.

1. Create the CloudFormation output file using the AWS CLI.  Using the commands below, you can either preset the \$AWS_PROFILE, \$REGION, \$CFN_S3_BUCKET, \$ML_FEEDBACK_S3_BUCKET_NAME, \$TRAININGJOBNAME_CONTAINS,\$THINGNAME and \$CERTIFICATE_ID variables, or reference those directly via the `aws cloudformation package` command. The result of that command will be an *OUTPUT* CloudFormation template file, along with the packaged Lambda functions being copied to the S3 bucket. The `AWS_PROFILE` contains the credentials, account details, and optionally region to create the CloudFormation stack.

   Complete list of commands to create the CloudFormation template file, upload assets, and create a stack (note the changes for the `--parameter-overrides` section).
   
   ```bash
    # BASH commands (replace exports with your AWSCLI profile, region, and S3 bucket settings)
    # AWS_PROFILE contains permissions to fully create and launch the CloudFormation package and template
    export AWS_PROFILE=<your-profile-here, e.g. default>
    export AWS_REGION=<your-region, e.g. us-east-1>

    # S3 bucket name without s3:// or https://
    export CFN_S3_BUCKET=<your_s3_bucket_that_holds_cloudformation, e.g. AccountId-cloudformation-us-east-1>

    # S3 model URI, which requires either S3:// or https://
    export ML_S3_BUCKET_URI=<s3 uri of the model that you obtained from steps "Required parameter for next step" above>

    # Create a AWS IoT Thing with name that ends with _Core, such as Toradex2_Core. 
    # Take note of the _Core because the Cloudformation will append _Core to the THINGNAME
    # Enter the ThingName below. In this example, the Thing Name is Toradex2
    export THINGNAME=<Thing name of the device to be the GreenGrass Core>
    export CERTIFICATE_ID=<Certificate ID>
    export STACK_NAME=<Cloudformation stack name>
                                                
    # Clean up any previously created files
    rm *-OUTPUT.yaml
    aws2 cloudformation package \
    --template-file cfn/mli_accelerator_dlr_models-INPUT.cfn.yaml \
    --output-template-file mli_accelerator_dlr_models-OUTPUT.yaml \
    --s3-bucket ${CFN_S3_BUCKET} --profile ${AWS_PROFILE} --region ${AWS_REGION}
      
    # If using the AWS Console, upload the mli_accelerator_s3_models-OUTPUT.yaml and continue with the parameters.
    # Below are the steps to deploy via the command line.
      
    # To deploy back-end stack from CLI (change --stack-name and --parameter-overrides to expected values)
    aws2 cloudformation deploy \
      --profile ${AWS_PROFILE} \
      --region ${AWS_REGION} \
      --stack-name ${STACK_NAME} \
      --template mli_accelerator_dlr_models-OUTPUT.yaml \
      --capabilities CAPABILITY_NAMED_IAM \
      --parameter-overrides \
        CoreName=${THINGNAME} \
        CertIdParam=${CERTIFICATE_ID} \
        ModelS3Uri=${ML_S3_BUCKET_URI}   
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
   --stack-name ${STACK_NAME} \
   --output text \  
   --query 'Stacks[*].Outputs[?OutputKey==`GreengrassConfig`].OutputValue' 
   ```
   or you can pipe through a Python json tool for pretty print:
   ```bash
   aws cloudformation describe-stacks \
   --stack-name ${STACK_NAME} \
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

For the Greengrass Feedback Connector, we created 3 configurations:
1. A random sampling at rate of 0.5
2. A strategy when the confidence of prediction lower than 0.5, 
3. One based on entropy with threshold 1.0

```
{
  "RandomSamplingConfiguration\":{
    "s3-bucket-name": "${FeedbackS3BucketName}",
    "file-ext": "png,jpg",
    "content-type": "image/jpeg,image/png",
    "sampling-strategy":{
        "strategy-name": "RANDOM_SAMPLING",
        "rate": 0.5
    }
  },
  "LC50": {
    "s3-bucket-name": "${FeedbackS3BucketName}",
    "s3-prefix": "confidence-lower-than-50",
    "content-type": "image/jpeg,image/png",
    "sampling-strategy": {
      "strategy-name": "LEAST_CONFIDENCE",
      "threshold": 0.5
    }
  },
  "Entropy": {
    "s3-bucket-name": "${FeedbackS3BucketName}",
    "s3-prefix": "entropy",
    "content-type": "image/jpeg,image/png",
    "sampling-strategy": {
      "strategy-name": "ENTROPY",
      "threshold": 1.0
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

If you noticed that `memUsed` is higher than the allocated memory `memSize` for either the connector or Lambda function, the function will not be started. Try increase the memory allocated for that function.

```
[2019-08-28T21:29:03.757Z][WARN]-Worker consumed all allocated memory! Memory Usage (KB).	{"workerId": "e544111a-03f5-40da-5e5c-23df2f6ced65", "funcArn": "arn:aws:lambda:<AWS Region>:<AWS Account ID>:function:pinned-ggc-mli-stack:6", "memSize": 120000, "memUsed": 165172}
[2019-08-28T21:29:03.757Z][ERROR]-Worker is ungracefully killed.	{"workerId": "e544111a-03f5-40da-5e5c-23df2f6ced65", "funcArn": "arn:aws:lambda:<AWS Region>:<AWS Account ID>:function:pinned-ggc-mli-stack:6", "state": "signal: killed"}
```

### Connector failed to start

If your deployment failed and the message is that certain worker failed to initialize, such as message below, check the logs for each functions. For custom Lambda function, the logs are in `/greengrass/ggc/var/log/user/<region>/<account ID>/<function name>.log`, and for connectors the logs are in `/greengrass/ggc/var/log/user/<region>/aws/<connector name>.log`.

```
Deployment 1a440a27-79b1-4346-80fb-934bf8a9bdfe of type NewDeployment for group 82a09694-0be7-4316-9c0a-a64fec972941 failed error: worker with e95c3577-1155-4127-55ec-2b0fedf3b121 failed to initialize
```

One of the cause could be the missing dependencies. For example, the log of the Image Classification might have the following message. 

```
[2020-02-20T01:05:20.372Z][FATAL]-lambda_runtime.py:140,Failed to import handler function "handlers.handler" due to exception: libgfortran.so.3: cannot open shared object file: No such file or directory
```

To resolve the issue, install the dependency as required with command `$ sudo apt-get install -y libgfortran3`
