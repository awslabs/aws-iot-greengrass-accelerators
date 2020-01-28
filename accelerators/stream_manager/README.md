# AWS IoT Greengrass Stream Manager

This Greengrass accelerator demonstrates the use of the [AWS IoT Greengrass stream manager](https://docs.aws.amazon.com/greengrass/latest/developerguide/stream-manager.html) (stream manager) feature as depicted in the [stream manager section](https://aws.amazon.com/blogs/aws/new-aws-iot-greengrass-adds-docker-support-and-streams-management-at-the-edge/) of the blog post.

Common use cases for stream manager include:

- Local video processing
- Image recognition
- High-volume data collection
- Handles disconnected or intermittent connectivity scenarios
- Prioritization of data path to the cloud for multiple streams


## Stream Manager Use Case

![Stream Manager and Docker Container](docs/stream-manager-architecture.png)

In this use case, we create two **Local data streams**, with the first stream configured for low-priority export to AWS IoT Analytics and a set amount of local disk space and overwriting the old data. The second stream is exporting data with high priority to an Amazon Kinesis Data Stream, again with a set amount of local disk space, but without overwriting data.

There are three deployed Lambda functions that serve different purposes:

- Producer Function - Reads sensor data (simulated) at high volume (60 readings per-second) and writes it to the Local Data Stream
- Aggregator Function - Reads the Local Data Stream, aggregates the data by creating an average per sensor every second, then writes the aggregate message to the Aggregated Local Data Stream
- Reader Container-based App - A Flask web application running in a Docker container that reads from the *Aggregated Local Data Stream*, displaying the aggregated information. The Reader also serves as an on/off switch for the simulated sensor data.

The two streams are used locally and export the data to AWS IoT Analytics for the raw data, and to Amazon Kinesis Data Streams for the aggregated data.

## Design Pattern

To demonstrate both Stream Manager and the Greengrass Docker application deployment connector, a Lambda function is created to generate test sensor data, which is then read by the *Producer Function* and processed as described above. The data is sent AWS IoT Analytics and an Amazon Kinesis Data Stream in the cloud.

The Stream Manager creates and persists the data locally, and sends to the cloud when there is connectivity. the Flask application is use to enable and disable the sensor data, and to show the aggregated local data stream.

TODO: image - GG as host and GG as containers

Greengrass can execute as either daemon on a host (Docker optional) or as a Docker container. All functionality is available in both methods, with the exception that when running as a container, all Docker-related actions are managed by the `dockerd` daemon at the host level.

This accelerator has been designed to run within a Docker container and utilizing the hosts Docker daemon to run Greengrass *and* the contents of the `docker-compose` file sent to Greengrass. In this manner, the accelerator can run on any host with Docker support installed. It can also be modified to run on an existing Greengrass 1.10.0 or newer installation by not running the initial `docker-compose.yml` file.

there is a local Cloud Development Kit (CDK) script to deploy a CloudFront stack and create the local assets required, such as the certificate and key pair used by the Greengrass core. The second component is a Docker compose file that runs Greengrass locally.


## Folder Structure

```text
stream_manager/
├── README.md                          <-- This file!
├── cdk
│   ├── etl_accelerator-INPUT.cfn.yaml <-- CloudFormation template
│   ├── lambda_functions
│   └── other_files
├── gg_docker                          <-- Creates Greengrass instance as container
│   ├── Dockerfile-greengrass
│   ├── certs
│   ├── config
│   ├── data
│   ├── docker-compose.yml
│   └── log
├── docs
└── test
```

There are two main components to using the accelerator. The `cdk/` directory contains the CDK assets to create the Greengrass configuration and long-lived Lambda functions as a *Greengrass deployment*. The *deployment* then waits for the target system, in this case a docker container, to start.

The `gg_docker/` directory container the assets to create a Docker image and running container with the dependencies to run the Greengrass deployment. It also has directories to hold the Greengrass configuration and credentials for the Greengrass Core.

## How to Deploy the Accelerator

To launch this accelerator as a Docker container, there are a few prerequisites and steps to complete. It is assumed you have basic experience with AWS IoT via the console and CLI.

The main steps for deployment are:

1. *Complete prerequisites*.
1. *Generate and launch the CloudFormation stack*. This will create the Lambda functions, the Greengrass resources, and an AWS IoT thing to be used as the Greengrass Core. The certificate will be associated with the newly created Thing. At the end, a Greengrass deployment will be created and ready to be pushed to the Docker container.
1. *From CloudFormation output, create the `config.json` file*. Then place all files into the `gg_docker/certs` and `gg_docker/config` directories.
1. *Run the container*. From the `gg_docker/` directory, launch (`docker-compose --build up`) to build the container, which will start Greengrass in a pre-deployed state.
1. *Deploy to Greengrass*. From the AWS Console, perform a Greengrass deployment that will push all resources to the Greengrass container and start the ETL operations.

When finished, stopping the accelerator (`CTRL-C` followed by `docker-compose down`) will gracefully stop all containers and then remove then. The deployment state and any persisted data will be preserved in the `docker/` subdirectories, and used when restarted.

### Verify Prerequisites

The following is a list of prerequisites to deploy the accelerator:

* AWS Cloud
  * Ensure you have an AWS user account with permissions to manage `iot`, `greengrass`, `lambda`, `cloudwatch`, and other services during the deployment of the CloudFormation stack.
  * Install the [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) and perform a [bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/troubleshooting.html#troubleshooting_nobucket) in the region you will be working.
  * Verify Docker Desktop or Docker Machine installed, and you have the ability to create or download images locally and run containers.
  * Ensure a recent version of the AWS CLI is installed and a user profile with permissions mentioned above is available for use.

### Create and Launch the CloudFormation Stack

:bulb: All steps below use a Cloud9 IDE in the same account and region where the accelerator will be run. If running locally, ensure you have the AWS CLI installed, and change the AWS profile name, *default*, to one with proper permissions.

Prior to launching the accelerator container locally, the AWS CDK is used to generate a CloudFormation template and deploy it. From Cloud9, follow the steps to create and launch the stack via the CDK.

1. *Pre-requisite* (only needs be run once) - Create a Cloud9 environment (t3.small), open a new Terminal window and run these commands:

   ```bash
   npm install -g aws-cdk
   git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git
   cd ~/environment/aws-iot-greengrass-accelerators/accelerators/stream_manager/cdk
   ```

1. Modify the 

1. Create the CloudFormation output file using the AWS CLI.  Using the commands below, replace or set these environment variables:

    * **\$AWS_PROFILE** - Reference an AWS CLI profile in `~/.aws` with the account credentials needed to build and deploy the CloudFormation template.
    * **\$REGION** - The AWS region for deploying the stack.
    * **\$S3_BUCKET** - A pre-created S3 bucket to hold the CloudFormation artifacts (e.g., Lambda function zip files).

   Below is a list of the commands to create the CloudFormation template file, upload assets, and create a stack (note the changes for the `--parameter-overrides` section where you need to provide the `ThingName` and `CertificateArn` values).
   
   ```bash
   # BASH commands (replace exports with your AWSCLI profile, region, and S3 bucket settings)
   # AWS_PROFILE contains permissions to fully create and launch the CloudFormation package and template
   export AWS_PROFILE=your-profile-here
   export REGION=us-west-2
   export S3_BUCKET=your_s3_bucket_here         # Needs to be located in same region as where
                                                # the CloudFormation stack is created.
   # Clean up any previously created files
   rm *-OUTPUT.yaml
   aws cloudformation package --template-file etl_accelerator-INPUT.cfn.yaml --output-template-file etl-accelerator-OUTPUT.yaml --s3-bucket $S3_BUCKET --profile $AWS_PROFILE --region $REGION
     
   # If using the AWS Console, upload the etl-accelerator-OUTPUT.yaml and continue with the parameters.
   # Below are the steps to deploy via the command line.
     
   # To deploy back-end stack from CLI (change --stack-name and --parameter-overrides to expected values)
   aws cloudformation deploy \
     --region $REGION \
     --stack-name greengrass-etl-accelerator \
     --template etl-accelerator-OUTPUT.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
       ThingName="gg_etl_accel" \
       CertificateArn="certificate ARN from prerequisites"
   
   # Output of stack deploy command:
   Waiting for changeset to be created..
   Waiting for stack create/update to complete
   Successfully created/updated stack - greengrass-etl-accelerator
   ```

At this point, all resources have been created and an initial Greengrass deployment has also been created and ready to be sent to the device.

### Configure and Launch the Docker Container

With the stack deployed, we use one output from the CloudFormation stack, the *GreengrassConfig* value, along with the certificate and private key to complete the `config.json` so that Greengrass in the Docker container can connect and authenticate.

1. Change to the the `docker/` directory.

1. Copy over the certificate and private key files to the `certs` directory. Copy the full file names to a temporary text file for modifying the `config.json` file.

1. Download to `certs` directory the [Amazon Root CA1](https://www.amazontrust.com/repository/AmazonRootCA1.pem) root certificate authority file used to verify the AWS IoT and AWS Greengrass endpoints. If the link opens with the contents in your browser, use alt-click and *Save As…* instead and save as `certs/AmazonRootCA1.pem`.

1. Change to the to `docker/config` directory and create a new file named `config.json`. From the CloudFormation console, select the stack and output tab. Copy the entire contents of the *GreengrassConfig* value, including the opening and close braces. Use your favorite JSON formatting tool to "prettify" the content. If you are using Linux or macOS with `jq` installed, the following will query and format the `config.json` content for you:

    ```bash
    $ aws --region $REGION cloudformation describe-stacks --stack greengrass-etl-accelerator | jq '.Stacks | to_entries | .[].value.Outputs | .[].OutputValue | fromjson'
    
    # Output
    {
      "coreThing": {
        ...
      }
    }
   ```
   
1. Paste into the newly created `config.json` file and replace *CERTIFICATE_NAME_HERE* with the file name and extension of your certificate (e.g., `123beef-certificate.pem.crt`).

1. Do the same replacing *PRIVATE_KEY_FILENAME_HERE* with the name of your private key (e.g., `123beef-private.pem.key`).

1. Save the file.

1. Change back to the `docker/` directory.

At this point, the Docker configuration has the details needed to start the containers and connect to AWS IoT Core and AWS Greengrass. Using `docker-compose` in the foreground, verify that the containers start and you are receiving startup log entries:

:exclamation: The first build may take a long time to complete as it installs dependencies. Further runs will use the locally created image so startup time will be shortened.

```bash
$ docker-compose up --build
Building greengrass
Step 1/9 : FROM amazon/aws-iot-greengrass:latest
...
Successfully tagged x86_64/greengrass-accelerator-etl:latest
Creating etl-greengrass ... done
Attaching to etl-greengrass
etl-greengrass | Starting Redis locally
etl-greengrass | Setting up greengrass daemon
etl-greengrass | Validating hardlink/softlink protection
etl-greengrass | Waiting for up to 1m10s for Daemon to start
etl-greengrass |
etl-greengrass | Greengrass successfully started with PID: 17
```

8. From the Greengrass Console, navigate to your created Greengrass Group and perform *Actions->Deploy* to deploy to the running Docker container.

To verify operation, you can look at the log files `docker/log/user/…/` for the Lambda functions for messages. Also, the S3 bucket used by Firehose should start to receive events. And, every 30 seconds, statistical messages will start to be published on the MQTT topic `core_name/telemetry` (default being `gg_etl_accel/telemetry`).

### Visualizing the Data

By downloading a Firehose create file from the S3 bucket, you can view the contents and see that this is all the messages, each as a single JSON message per-line.

Using Amazon Athena, modify the following SQL and run the query to create a database and table from your Firehose S3 bucket:

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS default.gg_etl (
  `pid` string,
  `value` float,
  `units` string,
  `source` string,
  `timestamp` timestamp 
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://greengrass-etl-accelerator-firehose-events-NNNNNNNN/firehose/'
TBLPROPERTIES ('has_encrypted_data'='false');
```

Once create, you can then directly query the data from Amazon Athena, or use the database and table as a data source for Amazon QuickSight. Here is an Amazon Athena query of vehicle speed, limited to first 10 records:

```sql
SELECT * FROM default.gg_etl WHERE pid = 'VehicleSpeed'
LIMIT 10
```

It will return something similar to this:

![Amazon Athena query results](docs/etl_athena_query.png)

## Modifications

The most common modifications would be to replace the code for three Lambda functions with code specific for your use case. To modify, start with the *Extract* function, view the contents of the *Extract Queue*, and then continue in a similar manner with the *Transform* and *Load* functions based on the *Load Queue*.

## FAQ and Help

### The `docker-compose` command shows `etl-greengrass exited with code 143`

#### Resolution

   1. Check that the certificate and private key files are in the correct location, and they are referenced by the correct names in the `config.json` file.
   1. Ensure there is at least one Lambda function defined within the Greengrass group and that all container-based settings such as Isolation mode are set properly.
