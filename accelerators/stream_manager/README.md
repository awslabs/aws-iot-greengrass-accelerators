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

In this use case, we create two **local data streams**, with the first stream, *LocalDataStream*, configured for low-priority export to AWS IoT Analytics and a set amount of local disk space and overwriting the old data. The second stream, *AggregateDataStream*, exports data with high priority to an Amazon Kinesis Data Stream, again using local resources for data persistence.

There are three deployed Lambda functions and a Greengrass managed Docker container that serve different purposes:

- **Sensor Source Function** - Generates simulated data for use by the rest of the accelerator.
- **Stream Producer Function** - Reads sensor data at high volume (20 readings per-second) and writes it to the *LocalDataStream*.
- **Stream Aggregator Function** - Reads the *LocalDataStream*, aggregates the data by creating an average per sensor every five seconds, then writes the aggregate message to the *AggregateDataStream*.
- **Greengrass Managed Docker Container** - A Flask web application running in a Docker container that reads the aggregate values from the *Stream Aggregator Function*, displaying the aggregated information.

The two streams are used locally and also export the data to AWS IoT Analytics for the raw data, and to Amazon Kinesis Data Streams for the aggregated data.

## Design Pattern

To demonstrate both Stream Manager and the Greengrass Docker application deployment connector, a Lambda function is created to generate test sensor data, which is then read by the *Producer Function* and processed as described above. The data is sent AWS IoT Analytics and an Amazon Kinesis Data Stream in the cloud.

The Stream Manager creates and persists the data locally, and sends to the cloud when there is connectivity. The Greengrass managed container, a web Flask application, displays the aggregate data from the Stream Aggregator function.

TODO: image - GG as host and GG as containers

Greengrass can execute as either daemon on a host (Docker optional) or as a Docker container. All functionality is available in both methods, with the exception that when running as a container, all Docker-related actions are managed by the `dockerd` daemon at the host level.

This accelerator has been designed to run within a Docker container and utilizing the hosts Docker daemon to run Greengrass *and* the contents of the `docker-compose` file sent to Greengrass. In this manner, the accelerator can run on any host with Docker support installed. It can also be modified to run on an existing Greengrass 1.10.0 or newer host installation by not running the initial `docker-compose.yml` file, by using the `config.json`, certificate and private keys.

There is a local Cloud Development Kit (CDK) script to deploy a CloudFront stack, and a Python script to create the local assets required, such as the certificate and key pair used by the Greengrass core. The second component is a Docker compose file that runs Greengrass locally.


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

### Prerequisites

The following is a list of prerequisites to deploy the accelerator:

  * Ensure you have an AWS user account with permissions to create and manage `iot`, `greengrass`, `lambda`, `cloudwatch`, and other services used by CloudFormation (CDK).
  * Install the AWS CLI locally and create a [named profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) with credentials for the AWS user account. For Cloud9, there is a profile already created named *default*.
  * Install the [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) and perform a [bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/troubleshooting.html#troubleshooting_nobucket) in the region you will be working.
  * Verify Docker Desktop or Docker Machine installed, and you have the ability to create or download images locally and run containers.

### Create and Launch the CloudFormation Stack

:bulb: All steps below use a Cloud9 IDE in the same account and region where the accelerator will be run. If running locally, ensure you have the AWS CLI installed, and change the AWS named profile from *default* to one you have created with proper permissions.

Prior to launching the accelerator container locally, the AWS CDK is used to generate a CloudFormation template and deploy it. From Cloud9, follow the steps to create and launch the stack via the CDK.

1. *Pre-requisites* (only needs be run once) - Create a Cloud9 environment (t3.small), open a new Terminal window and run these commands:

    ```bash
    # Cloud9 Commands - change as needed for local development environment
    # Install pre-requisites, bootstrap CDK for use in account/region, and reboot
    npm uninstall -g cdk
    npm install -g aws-cdk@1.26.0
    # Bootstrap CDK for current AWS account and region where Cloud9 runs
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    cdk bootstrap aws://$ACCOUNT/$REGION
    sudo curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    # Enable soft/hard links
    sudo cat <<EOF | sudo tee /etc/sysctl.d/98-cloud9-greengrass.conf
    fs.protected_hardlinks = 1
    fs.protected_symlinks = 1
    EOF
    # Allow access to Cloud9 instance for local Flask app
    # Add inbound for port 80 to the flask app (80->8082)
    sudo /sbin/iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8082
    sudo /etc/init.d/iptables save
    aws ec2 authorize-security-group-ingress --group-name $(curl -s http://169.254.169.254/latest/meta-data/security-groups) --protocol tcp --port 80 --cidr 0.0.0.0/0
    sudo reboot


    # After reboot open a new terminal window and issue these commands
    # NOTE: If terminal window spins when restarted, close the terminal window and launch a new one
    cd ~/environment
    # Clone the repository
    git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git
    cd ~/environment/aws-iot-greengrass-accelerators/accelerators/stream_manager/cdk

    # Build and deploy the CDK (CloudFormation stack)
    npm install
    npm run build
    cdk --profile default deploy

    # Acknowledge the creation above, then run
    python3 deploy_resources.py -p default

    # Build and start the Greengrass docker container
    cd ../gg_docker
    docker-compose build
    docker-compose up -d
    ```

1. At this point, the CloudFormation stack has been deployed and the Greengrass container is running. The CloudFormation stack will also trigger an initial deployment of all resources, so the Lambda functions, Stream Manager, and docker containers are also running.

1.  :exclamation: The Docker containers run as the root process in Cloud9 (and other Linux environments). If you wish to look at log or deployment files locally, it is easiest to launch another terminal tab and set that user to root:

    ```bash
    sudo su -
    cd ~ec2-user/environment/aws-iot-greengrass-accelerators/accelerators/stream_manager/gg_docker/
    # You can now cat|more|less|tail files from here
    tail -F log/system/runtime.log
    ...
    ```



## Modifications



## FAQ and Help

### Error seen

#### Resolution

   1. step 1
   1. step 2

## Implementation Notes

Technical details on how the different accelerator components run.

### MQTT Topics, Messages, and Lambda Actions

Different components use either MQTT topics or direct IPC calls to query and command each other.

### Lambda Functions

Details on Lambda Functions and How They Operate

#### sensor-source

This is a long running Lambda that generates and publishes simulated sensor data to a local stream. It also exposes a simplistic API for turning on and off the sensor data. the API listens on port 0.0.0.0:8180 (this port is opened on the Cloud9 instance).

