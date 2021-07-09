# AWS IoT Greengrass V2 Base Implementation

This accelerator deploys a single instance of an AWS IoT Greengrass core device, an example component, and creates a deployment to the core device. Once completed and the local container started, a fully functional AWS IoT Greengrass environment will be running with developer tools included. [foo](http://dfssfd.com)

# Base Implementation Use Case

# Design Pattern

# Folder Structure

```text
stream_manager/
├── README.md                          <-- This file!
├── cdk
├── docker_compose_stack               <-- Compose stack to be managed by Greengrass
│   ├── docker-compose.yml
├── gg_docker                          <-- Creates Greengrass instance as container
│   ├── Dockerfile-greengrass
│   ├── certs
│   ├── config
│   ├── deployment
│   ├── docker-compose.yml
│   └── log
├── docs
└── test
```

There are two main components to using the accelerator. The `cdk/` directory contains the CDK assets to create the Greengrass configuration and long-lived Lambda functions as a _Greengrass deployment_.

The `gg_docker/` directory container the assets to create a Docker image and run Greengrass as a container locally. It also has directories to hold the Greengrass configuration and credentials for the Greengrass Core, along with the log files.

# Deploying the Accelerator

This accelerator is designed to deploy as a combination of AWS CloudFormation stacks in the cloud and as Docker containers on your local system or through [AWS Cloud9](https://aws.amazon.com/cloud9/). This provides a consistent and quick approach to testing or investigating functionality without impacting or leaving behind unneeded artifacts locally. To launch this accelerator as a Docker container, there are a few prerequisites and steps to complete. It is assumed you have basic experience with AWS IoT via the console and CLI.

## Prerequisites

The following is a list of prerequisites to deploy the accelerator:

- Ensure you have an AWS user account with permissions to create and manage `iot`, `greengrass`, `lambda`, `cloudwatch`, and other services used by CloudFormation.
- Install the AWS CLI locally and create a [named profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) with credentials for the AWS user account. For Cloud9, there is a profile already created named _default_.
- Install the [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) and perform a [bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/troubleshooting.html#troubleshooting_nobucket) in the region you will be working.
- Verify Docker Desktop for macOS or Microsoft Windows installed, or Docker Engine for Linux. Ensure you have the ability to create or download images locally and run containers.

There are two methods describe below:

- If you are familiar with Nodejs, Python and working with the command line on your local system, select the _Create and Launch the Accelerator Locally_ method.
- For all others, use the _Step-by-Step: Create and Launch the Accelerator via AWS Cloud9_ method.

## Create and Launch the Accelerator Locally

This approach uses your local system for installation and running the accelerator. It requires certain pre-requisites to be installed. If you like to run from a consistent environment, see the next section for deploying using AWS Cloud9.

<details>
<summary>Click here to show/hide the steps to run locally</summary>
<br>
:bulb:These steps assume familiarity with installation of NPM/NPX,  Nodejs packages, Python, and working from the command line interface (CLI).

1. Install and bootstrap the CDK:

   ```bash
   npx install -g aws-cdk
   export CDK_DEPLOY_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
   # Set REGION to where the accelerator will be installed
   export CDK_DEPLOY_REGION=us-east-1
   cdk bootstrap aws://$CDK_DEPLOY_ACCOUNT/$CDK_DEPLOY_REGION
   ```

1. Clone the repository, change into the `cdk/` directory, then build and deploy the CloudFormation stack:

   ```bash
   git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git
   cd aws-iot-greengrass-accelerators/vs/base_implementation/cdk
   npm install
   npm run build
   # Set region for deployment (optional if the AWS CLI profile has the region set to where you want to deploy)
   export CDK_DEPLOY_REGION=us-east-1
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region
   cdk --profile PROFILE_NAME deploy
   ```

1. At this point the CloudFormation stack is deployed. Next, run the `deploy_resources.py` script, which will:

   1. Read the local CDK output to determine the CloudFormation stack name
   1. From the CloudFormation stack output, read the values to:
      1. Create the `config.json` file for Greengrass in the `stream_manager/gg_docker/config` directory
      1. Create the `certificate.pem` and `private_key.pem` files in the `stream_manager/gg_docker/certs` directory
   1. And finally upload the `stream_manager/docker_compose_stack/docker-compose.yml` file to the S3 directory referenced by the Greengrass Docker Application Deployment Connector.

   ```bash
   python3 deploy_resources.py -p default
   ```

1. Next, change to the `stream_manager/gg_docker` directory and start Greengrass running as Docker container. If you intend to run Greengrass on a physical device, copy the contents of the `stream_manager/gg_docker/certs` and the `stream_manager/gg_docker/config` directories to your core (e.g., `/greengrass/certs` and `/greengrass/config`).

   ```bash
   cd ../gg_docker
   # Build from the latest published version of Greengrass
   docker pull amazon/aws-iot-greengrass:1.11.3-amazonlinux-x86-64
   docker-compose build
   docker-compose up -d
   ```

At this point, the CloudFormation stack has been deployed and the Greengrass container is running. The CloudFormation stack will also trigger an initial deployment of all resources to the Greengrass Core, so the Lambda functions, Stream Manager, and docker containers are also running.

Greengrass will start to write files into the `gg_docker/log` directory, and the web interface to the Flask application can be locally accessed via http://localhost:8082 (IP address dependent on your local Docker process).

</details>

## Step-by-Step: Create and Launch the Accelerator via AWS Cloud9

<details>
<summary>Click here to show/hide the steps to run via AWS Cloud9</summary>
<br>

:bulb: All steps below use a Cloud9 IDE in the same account and region where the accelerator will be run. If running locally, ensure you have the AWS CLI installed, and change the AWS named profile from _default_ to one you have created with proper permissions.

Prior to launching the accelerator container locally, the AWS CDK is used to generate a CloudFormation template and deploy it. From Cloud9, follow the steps to create and launch the stack via the CDK.

1.  Create a new Cloud9 IDE and make sure that **Amazon Linux 2** and **t3.small** are selected.

    :exclamation:The following steps **will not** work if Ubuntu is selected.

1.  Once the Cloud9 environment starts, follow [these steps](https://docs.aws.amazon.com/cloud9/latest/user-guide/move-environment.html#move-environment-resize) to resize the disk. Create the `resize.sh` file and run `bash resize.sh 40` to extend the disk to 40GiB.

1.  _Pre-requisites_ (only needs be run once and the environment will reboot) - Open a new Terminal window and run these commands:

    ```bash
    # Cloud9 Commands - change as needed for local development environment
    # Install pre-requisites, bootstrap CDK for use in account/region, and reboot
    npm uninstall -g cdk
    npm install -g aws-cdk@latest
    sudo yum install iptables-services -y
    # Bootstrap CDK for current AWS account and region where Cloud9 runs
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    cdk bootstrap aws://$ACCOUNT/$REGION
    sudo curl -L "https://github.com/docker/compose/releases/download/1.25.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    pip3 install --user boto3
    # Enable soft/hard links
    sudo cat <<EOF | sudo tee /etc/sysctl.d/98-cloud9-greengrass.conf
    fs.protected_hardlinks = 1
    fs.protected_symlinks = 1
    EOF
    # Allow access to Cloud9 instance for local Flask app
    # Add inbound for port 80 to the flask app (80->8082)
    sudo systemctl enable iptables
    sudo /sbin/iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8082
    sudo service iptables save
    aws ec2 authorize-security-group-ingress --group-name $(curl -s http://169.254.169.254/latest/meta-data/security-groups) --protocol tcp --port 80 --cidr 0.0.0.0/0
    sudo reboot
    ```

1.  Build and deploy. Once Cloud9 has restarted, issue these commands. If the terminal window is unresponsive, open a new one.

    ```bash
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
    docker pull amazon/aws-iot-greengrass:1.11.3-amazonlinux-x86-64
    docker-compose build
    docker-compose up -d

    # Get the IP address for accessing the Flask docker container once it is operational
    MY_IP=$(curl -s ifconfig.co)
    echo "This is the URL to access the Flask Container: http://$MY_IP"
    # Done!
    ```

1.  At this point, the CloudFormation stack has been deployed and the Greengrass container is running. The CloudFormation stack will also trigger an initial deployment of all resources to the Greengrass Core, so the Lambda functions, Stream Manager, and docker containers are also running.

    Greengrass will start to write files into the `gg_docker/log` directory, and the web interface to the Flask application can be accessed via the returned URL on the _This is the URL to access..._ line above.

1.  :exclamation: The Docker containers run as the root process in Cloud9 (and other Linux environments). If you wish to look at log or deployment files locally, it is easiest to launch another terminal tab and set the user to root:

    ```bash
    sudo su -
    cd ~ec2-user/environment/aws-iot-greengrass-accelerators/accelerators/stream_manager/gg_docker/
    # You can now cat|more|less|tail files from here
    tail -F log/system/runtime.log
    ...
    ```

    </details>

## Investigating the Accelerator

TODO: Information on what, why, and how the accelerator works by subsection.

## Accelerator Cleanup

TODO: common steps for clean up and then add specifics for accelerator.

To stop and completely remove this accelerator, follow these steps:

1. From the command line, either locally on in Cloud 9, stop the Greengrass container:

   ```bash
   docker-compose down
   ```

1. With the container stopped, change to the CDK directory and issue the command to _destroy_ the CloudFormation stack:

   ```bash
   cd ../cdk
   # For Cloud9
   cdk --profile default destroy
   # For locally running (replace PROFILE_NAME with one used to create stack)
   cdk --profile PROFILE_NAME destroy
   ```

   If there are any errors abut not being able to completely destroy the stack, review the error messages and resolve. In most cases it will be related to assets that may have been modified. Once resolve, run the `cdk destroy` command again, or delete the stack from the CloudFormation console.

   Also, at this point the certificate and private key are no longer valid in the Greengrass `certs/` directory. If you wish to redeploy the stack, clear out all of the `certs/` and `config/` directories,

1. If you created any assets that references or used AWS IoT Analytics or Amazon Kinesis Data Streams such as a Kinesis Analytics Application, delete these also.

1. Review any CloudWatch Logs log groups and delete these if needed.

1. Finally, change out of the GitHub repository and fully delete the directory.

That's it! Fully deployed, ran, and cleaned up!

## Frequently Asked Questions

### Question name

Supporting details or answer

#### Resolution (optional)

Steps to resolve issue

## Implementation Notes

Technical details on how the different accelerator components run.
