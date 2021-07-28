# AWS IoT Greengrass V2 Base Implementation

This is the base accelerator that deploys a single instance of an AWS IoT Greengrass core device and all supporting resources for operation, including:

- Thing - Virtual representation of the Greengrass core device (along with certificate and private key)
- Thing group - The thing is part of this group and the target for the Greengrass deployment
- IoT Core role alias - Used by the credential provider to vend AWS credentials to Greengrass components
- IAM role - Referred to by the role alias, contains the inline IAM policy of minimal permissions for the Greengrass core device
- Greengrass component - An example component (recipe and artifacts) deployable to Greengrass cores. Part of the Greengrass deployment
- Greengrass deployment - A list of public and private components targeting the members of the thing group

Once this is fully deployed, a fully functional AWS IoT Greengrass environment will be running via a Docker container with the components deployed and running on the Greengrass core device.

All other version 2 accelerators leverage the resources created by this stack, then extend them by creating additional components, a thing group specific to the other accelerators, and a deployment that targets the new thing group.

# Base Implementation Use Case

This accelerator demonstrates the ability to automate the creation and deployment of resources for a complete Greengrass implementation. It is a prerequisite for all other version 2 accelerators, utilizing the same Greengrass core device.

# Design Pattern

The following architecture shows the process flow for deploying the accelerator.

![Base Implementation Process Steps](docs/arch1.svg)

1. CDK is used locally to create the CloudFormation stack and deploy to the cloud.
1. The stack creates all the resources for the accelerator. Of note, the _Deployment_ targets the _Thing Group_ where the Greengrass core device resides.
1. Locally, the `config_docker.py` script is run to populate the _certs_ and _config_ directories from the local CDK stack and CloudFormation output in the cloud.
1. When the local Docker container is started, it reads the configuration settings and then receives the _Deployment_ from the cloud.

# Folder Structure

```text
base
├── README.md             <--- this file
├── cdk                   <--- builds and deploys CloudFormation to cloud
│   ├── bin
│   ├── cdk.json
│   ├── components
│   ├── jest.config.js
│   ├── lib
│   ├── package-lock.json
│   ├── package.json
│   ├── test
│   └── tsconfig.json
└── docker                <--- configures and runs Greengrass as a container
    ├── config_docker.py
    ├── templates
    └── volumes
```

There are two main aspects to using the accelerator. First, from the `cdk/` directory is used to build and deploy a complete AWS IoT Greengrass stack in the cloud. Once complete, all resources exist in the cloud and are available for the next step which is configuring and running Greengrass locally.

The second step is running commands from the `docker/` directory once the stack has been deployed. First, running `python config_docker.py` will populate the initial configuration file and download the credentials for AWS IoT Greengrass to run. Then, `docker compose up` will start the core device and complete the deployment of resources.

# Deploying the Accelerator

> **NOTE:** All accelerators use the same structure and steps to deploy, even if the actual output of the steps differ slightly.

This accelerator is designed to deploy as a combination of AWS CloudFormation stacks in the cloud and run AWS IoT Greengrass as a Docker container on your local system or through [AWS Cloud9](https://aws.amazon.com/cloud9/). This provides a consistent and quick approach to testing or investigating functionality without impacting or leaving behind unneeded artifacts locally, or in the cloud. To launch this accelerator as a Docker container, there are a few prerequisites and steps to complete. It is assumed you have basic experience with AWS IoT via the console and have familiarity with the command line interface (CLI).

## Prerequisites

The following is a list of prerequisites to deploy the accelerator:

1. Ensure you have an AWS user account with permissions to create and manage resources. An Identity and Access Management (IAM) user with the [Administrator role](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html#jf_administrator) meets this requirement.
1. Install the AWS CLI locally and create a [named profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) with credentials for the AWS user account. For Cloud9, there is a profile already created named _default_ that will have your accounts permissions.
1. Install the [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) and perform a [bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/troubleshooting.html#troubleshooting_nobucket) in the region you will be deploying the accelerator.
1. Verify Docker Desktop for macOS or Microsoft Windows installed, or Docker Engine for Linux. Ensure you have the ability to create or download Docker images locally and run containers. The [Docker Compose tool](https://docs.docker.com/compose/) is required, either from Docker Desktop or installed separately.

There are two installation and deployment methods outlines below:

- If you are familiar with Nodejs, Python and working with the command line on your local system, select the [Create and Launch the Accelerator Locally](#create-and-launch-the-accelerator-locally) method.
- For all others, use the [Step-by-Step: Create and Launch the Accelerator via AWS Cloud9](#step-by-step-create-and-launch-the-accelerator-via-aws-cloud9) method.

## Create and Launch the Accelerator Locally

This approach uses your local system for installation and running the accelerator. It requires certain pre-requisites to be installed. If you like to run from a consistent environment, see the next section for deploying using AWS Cloud9.

<details>
<summary>Click here to show/hide the steps to run locally</summary>
<br>

> :bulb: These steps assume familiarity with installation of NPM/NPX, Nodejs packages, Python, and working from the command line interface (CLI).

1. Install and bootstrap the CDK:

   ```bash
   npx install -g aws-cdk
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined
   export CDK_DEPLOY_ACCOUNT=$(aws sts get-caller-identity --profile PROFILE_NAME --query Account --output text)
   # Set REGION to where the bootstrap resources will be deployed
   export CDK_DEPLOY_REGION=us-east-1
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined
   cdk --profile PROFILE_NAME bootstrap aws://$CDK_DEPLOY_ACCOUNT/$CDK_DEPLOY_REGION
   ```

1. Clone the repository, change into the `cdk/` directory for the accelerator, then build and deploy the CloudFormation stack:

   > **NOTE:** The first time `cdk deploy` is run, it will take longer as there are Docker images required to build some of the resources. You will see Docker-related messages in your terminal session. Subsequent runs will only take a few additional seconds.

   ```bash
   git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git
   cd aws-iot-greengrass-accelerators/vs/base_implementation/cdk
   npm install
   npm run build
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined
   cdk --profile PROFILE_NAME deploy
   ```

   The result of a successful deployment will look like this:

   ```bash
    ✅  base-implementation

   Outputs:
   base-implementation.CertificatePemParameter = /base-implementation/base-implementation-greengrass-core-FAjEi5wg/certificate_pem
   base-implementation.CredentialProviderEndpointAddress = c301XXXXXsf1qf.credentials.iot.us-west-2.amazonaws.com
   base-implementation.DataAtsEndpointAddress = a2l4XXXXXfczky-ats.iot.us-west-2.amazonaws.com
   base-implementation.IotRoleAliasName = base-implementation-GreengrassV2TokenExchangeRole-FAjEi5wg
   base-implementation.PrivateKeySecretParameter = /base-implementation/base-implementation-greengrass-core-FAjEi5wg/private_key
   base-implementation.ThingArn = arn:aws:iot:us-west-2:123456789012:thing/base-implementation-greengrass-core-FAjEi5wg
   Stack ARN:
   arn:aws:cloudformation:us-west-2:123456789012:stack/base-implementation/bc6f5210-ee18-11eb-a253-060b98b02c23
   ```

1. At this point the CloudFormation stack is deployed. Next, change to the `docker/` directory and run the configuration script (`python3 config_docker.py` script, which will:

   1. Read the local CDK output to determine the CloudFormation stack name
   1. From the CloudFormation stack output, read the values to:
      1. Download and save the X.509 certificate, private key, and Amazon CA1 certificate to the `volumes/certs` directory
      1. Using the stack outputs, generate and save an initial configuration file to `volumes/config`

   ```bash
   cd ../docker
   # Use the same AWS CLI profile from above
   python3 docker_config.py --profile PROFILE_NAME
   ```

1. Next, start the Greengrass core device. If you intend to run Greengrass on a physical device, copy the contents of the `volumes/certs` and the `volumes/config` directories to your physical device and provision and install Greengrass per the documentation.

   > **NOTE:** The first time `docker compose up` is run, it will take longer to startup as Docker will need to download the AWS IoT Greengrass image. Subsequent runs will only take a few additional seconds.

   ```bash
   docker-compose up
   ```

At this point, the CloudFormation stack has been deployed and the AWS IoT Greengrass container is running. Continue to the [Investigating the Accelerator](#investigating-the-accelerator) section for your accelerator for additional details.

The `volumes/gg_root` will contain the various Greengrass core device files. Of interest will be the log files located in `volumes/gg_root/logs`.

</details>

## Step-by-Step: Create and Launch the Accelerator via AWS Cloud9

<details>
<summary>Click here to show/hide the steps to run via AWS Cloud9</summary>
<br>

> :bulb: All steps below use a Cloud9 IDE in the same account and region where the accelerator will be run.

Prior to launching the accelerator container locally, the AWS CDK is used to generate a CloudFormation template and deploy it. From the AWS Cloud9 console, follow these steps to create and launch the stack via CDK.

1.  Create a new Cloud9 IDE and make sure that **Amazon Linux 2** and **t3.small** are selected.

    :exclamation:The following steps **will not** work if Ubuntu is selected.

1.  Once the Cloud9 environment starts, follow [these steps](https://docs.aws.amazon.com/cloud9/latest/user-guide/move-environment.html#move-environment-resize) to resize the disk. Create the `resize.sh` file and run `bash resize.sh 40` to extend the disk to 40GiB.

1.  _Pre-requisites_ (only needs be run once and the Cloud9 environment will reboot) - From the Cloud9 IDE, open a new _Window->New Terminal_ window and run these commands:

    ```bash
    # Cloud9 Commands - change as needed for local development environment
    # Install pre-requisites, bootstrap CDK for use in account/region, and reboot
    npm uninstall -g cdk
    npm install -g aws-cdk@latest
    npm install -g npm
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
    # Complete, reboot environment
    sudo reboot
    ```

1.  Build and deploy. Once Cloud9 has restarted, issue these commands. If the terminal window is unresponsive, open a new one.

    > **NOTE:** The first time `cdk deploy` is run, it will take longer as there are Docker images required to build some of the resources. You will see _a lot_ of Docker-related messages in your terminal session as it downloads and builds the initial resources. Subsequent runs will only take a few additional seconds.

    Run each command separately to get an understanding

    ```bash
    # After reboot open a new terminal window and issue these commands
    # NOTE: If terminal window spins when restarted, close the terminal window and launch a new one
    cd ~/environment
    # Clone the repository
    git clone https://github.com/awslabs/aws-iot-greengrass-accelerators.git
    # Change path to accelerator you wish to run. This accelerator, "base",
    # is shown below
    cd ~/environment/aws-iot-greengrass-accelerators/v2/base/cdk

    # Build and deploy the CDK (CloudFormation stack)
    npm install
    npm run build
    cdk deploy

    # Acknowledge the creation above, then run
    python3 deploy_resources.py -p default

    # Build and start the Greengrass docker container
    cd ../docker
    docker-compose up
    ```

1.  At this point, the CloudFormation stack has been deployed and the Greengrass container is running as a fore ground process in the terminal. The CloudFormation stack will also trigger an initial deployment of all resources to the Greengrass Core, so the Lambda functions, Stream Manager, and docker containers are also running.

1.  :exclamation: The Docker containers run as the root process in Cloud9 (and other Linux environments). If you wish to look at log or deployment files locally, it is easiest to launch another terminal tab and set the user to root:

    ```bash
    sudo su -
    cd /home/ec2-user/environment/aws-iot-greengrass-accelerators/v2/base/docker/gg_root/logs
    # You can now cat|more|less|tail files from here
    tail -F greengrass.log
    ...
    ```

    </details>

## Investigating the Accelerator

As a base accelerator, the main interaction with this accelerator is to ensure it is running correctly, understand the directory structure, and access various log files. You can review the output of the _Hello World_ example component by looking at the contents of the log file in `docker/volumes/logs/ggAccel.example.HelloWorld.log`.

Other accelerators use this stack's resources to build additional Greengrass components and deployments and a thing group. When the Docker container is restarted the Greengrass core device will merge all deployments into a single one.

## Accelerator Cleanup

To stop and completely remove this accelerator, follow these steps:

1. From the command line where Greengrass is running (the `docker-compose` command was started), either locally on in Cloud 9, stop the Greengrass container byt entering CTRL+C and then:

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

   Also, at this point the certificate and private key are no longer valid in the Greengrass `docker/volumes/certs` directory. If you wish to redeploy the stack, you can run the `python3 config_docker.py --clean` command to remove all configuration and Greengrass files.

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
