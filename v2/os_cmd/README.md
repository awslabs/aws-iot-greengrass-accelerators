# AWS IoT Greengrass V2 Operating System (OS) Command Component

This component extends the the capabilities of the [base](../base) accelerator stack by adding a new thing group, Greengrass component, and Greengrass deployment for the existing core. The functionality the `ggAccel.os_command` component provides is the ability to publish an operating system command via an MQTT message to a topic on AWS IoT Core, have it execute on the Greengrass core device, and return the commands output to a different MQTT topic. By publishing the command on topic and subscribing to the response on another topic, you can remotely issue commands and receive results via the cloud.

This is deployed as a [nested stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-nested-stacks.html) where the root stack is the base implementation accelerator. This stack creates the following resources:

- Thing group - A group specific to this accelerator, the existing thing is added and targeted for the new component
- IoT policy - An AWS IoT policy attached to the existing certificate extending the ability to publish and subscribe on the topics used by the component
- Greengrass component - The application logic (recipe and artifacts) deployable to Greengrass cores. Part of the Greengrass deployment.
- Greengrass deployment - The Greengrass component targeted for the new Thing group.

Once this is fully deployed, the Greengrass core device will receive and deploy the component immediately or when next started.

# OS Command Use Case

This accelerator demonstrates the capability for a local Python application to receive commands from the Cloud, run them locally, and then publish back the results to another topic in the Cloud. It demonstrates Cloud command and control capability to a remote device, the ability for a local application to interact with IPC topics, execute commands locally, and response to successful or unsuccessful commands.

In practical operation, it can be used to query the status of host operating system, download and upgrade software, or any other activities normally performed from the host operating systems command line interface (CLI). It can also be used as an example for performing command and control operations originating from the cloud and taking local action.

# Design Pattern

The following architecture shows the deployment of this accelerator (aligned to the base implementation).

![Base Implementation Process Steps](docs/arch1.svg)

1. The CDK stack creates a new thing group, adds the thing-core, and deploys the `os_cmd` component. The two thing group component lists are merges and sent to the Greengrass core.
1. The component starts and subscribes to a topic for incoming commands.
1. When a command is issued by a person or application it is sent to the component and run as a terminal command.
1. When the command has completed the component publishes the result back to the Cloud for the person or application to use.

# Folder Structure

```text
os_cmd
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
```

As a nested stack, this uses CDK to deploy. As it uses CDK constructs from the `base` stack via relative paths, do not move this directory without first updating the paths in `lib/OsCommandStack.ts` first.

If using Docker, continue to use the `base/docker` directory for starting and stopping the container.

# Deploying the Accelerator

> **NOTE:** All accelerators use the same structure and steps to deploy, even if the actual output of the steps differ slightly.

Use the steps from the _base implementation_ stack to deploy the CDK stack. These are the general steps to follow for both local and AWS Cloud9.

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

1. Change into the `v2/os_cmd/cdk/` directory for the accelerator, then build and deploy the CloudFormation stack:

   > **NOTE:** The first time `cdk deploy` is run, it will take longer as there are Docker images required to build some of the resources. You will see Docker-related messages in your terminal session. Subsequent runs will only take a few additional seconds.

   ```bash
   cd aws-iot-greengrass-accelerators/v2/os_cmd/cdk
   npm install
   npm run build
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined. Also note that the base stack name must be provided
   cdk --profile PROFILE_NAME deploy --context baseStack="gg-accel-base"
   ```

   The result of a successful deployment will look like this:

   ```bash
   ✅  gg-accel-os-command

   Outputs:
   gg-accel-os-command.RequestTopic = gg-accel-base-greengrass-core-1BFfAdXT/os_cmd/request
   gg-accel-os-command.ResponseTopic = gg-accel-base-greengrass-core-1BFfAdXT/os_cmd/response
   Stack ARN:
   arn:aws:cloudformation:us-west-2:123456789012:stack/gg-accel-os-command/82df9e50-fa21-11eb-ba37-02268e8a52f9
   ```

1. At this point the CloudFormation stack is deployed and if the Greengrass core is running, it will have received the new deployment. Copy the _Reqeust_ and _Response_ topics

1. At this point the CloudFormation stack is deployed. Next, change to the `docker/` directory and run the configuration script (`python3 config_docker.py` script, which will:

## Investigating the Accelerator

As a base accelerator, the main interaction with this accelerator is to ensure it is running correctly, understand the directory structure, and access various log files. You can review the output of the _Hello World_ example component by looking at the contents of the log file in `docker/volumes/gg_root/logs/ggAccel.example.HelloWorld.log`.

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
   cdk destroy
   # For locally running (replace PROFILE_NAME with one used to create stack)
   cdk --profile PROFILE_NAME destroy
   ```

   If there are any errors abut not being able to completely destroy the stack, review the error messages and resolve. In most cases it will be related to assets that may have been modified. Once resolve, run the `cdk destroy` command again, or delete the stack from the CloudFormation console.

   Also, at this point the certificate and private key are no longer valid in the Greengrass `docker/volumes/certs` directory. If you wish to redeploy the stack, you can run the `python3 config_docker.py --clean` command to remove all configuration and Greengrass files.

1. Review any CloudWatch Logs log groups and delete these if needed.

1. Finally, change out of the GitHub repository and fully delete the directory.

That's it! Fully deployed, ran, and cleaned up!

## Frequently Asked Questions

### How can I use this accelerator beyond the "Hello World" example component?

By creating a single core device, thing group, and deployment, you can create additional components external to the accelerator and then revise the Greengrass deployment that targets the thing group. This could be for cloud deployment testing or to investigate operationally how Greengrass handles deployment updates.

### How can I view the log file `/tmp/Greengrass_HelloWorld.log` referred to in the "Hello World" application code?

The full container file system can be accessed by executing a shell within the running container. To do so, with the container running via `docker compose up`, open a new terminal window locally or in Cloud9 and run these commands:

```shell
# Verify container name (default: greengrass-accel)
docker ps
CONTAINER ID   IMAGE          COMMAND                  CREATED      STATUS          PORTS                                       NAMES
fd53c272f65d   dafe85b8555c   "/greengrass-entrypo…"   2 days ago   Up 11 minutes   0.0.0.0:8883->8883/tcp, :::8883->8883/tcp   greengrass-accel

# Execute shell within the container ("bash-4.2#" is the shell in the container)
docker exec -it greengrass-accel /bin/bash
bash-4.2# cd /tmp
bash-4.2# cat Greengrass_HelloWorld.log
Hello, Welcome from the Greengrass accelerator stack! Current time: 2021-08-03 00:49:59.275648.
Hello, Welcome from the Greengrass accelerator stack! Current time: 2021-08-05 13:33:53.487968.
# Exit command will exit from the container back to your local terminal
bash-4.2# exit
exit
```

## Implementation Notes

The _Hello World_ component is a minimal python script to demonstrate component creation and deployment. In a normal operation, it will run once upon deployment or core device startup and create a log file in `/tmp` along with entries in the log file folder.
