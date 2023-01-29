# AWS IoT Greengrass V2 SiteWise Deployment

This deployment, SiteWise Deployment, extends the capabilities of the [base](../base) accelerator stack by adding a new thing group, and Greengrass deployment for the existing Greengrass core. The functionality of the Greengrass deployment leverages several AWS-provided components with the ability to ingest data from an OPC UA endpoint using a SiteWise gateway component and stream the data to IoT SiteWise.

This is deployed as a [nested stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-nested-stacks.html) where the root stack is the base implementation accelerator. This stack creates the following resources:

- Thing group - A group specific to this accelerator, the existing thing is added and targeted for the new component
- IoT policy - An AWS IoT policy attached to the existing certificate extending the ability to publish batch property values to IoT SiteWise
- Greengrass deployment - The Greengrass components targeted for the new Thing group.

Once this is fully deployed, the Greengrass core device will receive and deploy the required components immediately or when next started.

> **NOTE:** This accelerator is intended for educational use only and should not be used as the basis for production workloads without fully reviewing the component and it's artifacts.

## SiteWise Deployment Use Case

This accelerator demonstrates the capability for ingesting data from an OPC UA endpoint such in a factory, plant or other Operational Technology (OT) environment and streaming the data to [AWS IoT SiteWise](https://aws.amazon.com/iot-sitewise/).

In a practical setting, this appraoch can be used to collect and organise industrial data, by reading data directly from servers and historians over the OPC-UA protocol. Once ingested, data can be visualised and analysed to react to anomalises or identify differences across facilities.

For additional information on applicable use cases please explore the following workshops:

- [AWS IoT SiteWise Workshop](https://iot-sitewise.workshop.aws/en/introduction.html)
- [AWS IoT SiteWise Edge Workshop](https://iot-sitewise-edge.workshop.aws/)
- [IIoT Security Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/5b543f4c-1952-4bd9-96c8-b009c16da2bc/en-US)

## Design Pattern

The following architecture shows the deployment of this accelerator (aligned to the base implementation).

![SiteWise Deployment Architecture](docs/arch.svg)

1. The CDK stack creates a new thing group (`sitewise-group`), adds the existing `thing-core`, and deploys the required components. The two thing group deployments are merged and sent to the Greengrass core.
1. The OPC UA collector component starts and ingests data from the configured OPC UA endpoint.
1. The data are sent to the SiteWise edge publisher component via the local stream manager.
1. The SiteWise edge publisher component publishes the data to AWS IoT SiteWise, via the newly created SiteWise gateway associated with the Greengrass deployment.

## Folder Structure

```text
sitewise
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

As a nested stack, this uses CDK to build and deploy the resources. As it uses CDK constructs from the `base` stack via relative paths, do not move this directory without first updating the paths in `lib/SiteWiseStack.ts` first.

If using Docker, continue to use the `base/docker` directory for starting and stopping the container.

## Deploying the Accelerator

> **NOTE:** All accelerators use the same structure and steps to deploy, even if the actual output of the steps differ slightly.

Use the steps from the _base implementation_ stack to deploy the CDK stack. These are the general steps to follow for both local and AWS Cloud9.

This accelerator is designed to deploy as a combination of AWS CloudFormation stacks in the cloud and run AWS IoT Greengrass as a Docker container on your local system or through [AWS Cloud9](https://aws.amazon.com/cloud9/). This provides a consistent and quick approach to testing or investigating functionality without impacting or leaving behind unneeded artifacts locally, or in the cloud. To launch this accelerator as a Docker container, there are a few prerequisites and steps to complete. It is assumed you have basic experience with AWS IoT via the console and have familiarity with the command line interface (CLI).

### Prerequisites

The following is a list of prerequisites to deploy the accelerator:

1. The base implementation stack must be deployed. It is also recommended to configure and test the base implementation before deploying this stack.
1. The OPC UA endpoint details are available, such as the IP address and port. A typical OPC UA endpoint may look like `opc.tcp://10.0.0.10:62541/discovery`, in this case `10.0.0.10` is the IP address and `62541` is the port number.

### Create and Launch the Accelerator Locally

This approach uses your local system for installation and running the accelerator, but the same commands can be used if testing from AWS Cloud9.

1. Change into the `v2/sitewise/cdk/` directory for the accelerator, then build and deploy the CloudFormation stack:

   > **NOTE:** The first time `cdk deploy` is run, it will take longer as there are Docker images required to build some of the resources. You will see Docker-related messages in your terminal session. Subsequent runs will only take a few additional seconds.

   ```bash
   # Please note the need to substitute the real values for `OPC_UA_IP` and `OPC_UA_PORT` to construct a valid `OPC_UA_ENDPOINT` value.
   export OPC_UA_ENDPOINT=opc.tcp://OPC_UA_IP:OPC_UA_PORT/discovery
   cd aws-iot-greengrass-accelerators/v2/sitewise/cdk
   npm install
   npm run build
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined.
   # Also note that the base stack name must be provided.
   cdk --profile PROFILE_NAME deploy --context baseStack="gg-accel-base" --parameters opcUaEndpoint="${OPC_UA_ENDPOINT}"
   ```

   The result of a successful deployment will look like this:

   ```bash
   ✅  gg-accel-sitewise

   Stack ARN:
   arn:aws:cloudformation:us-west-2:123456789012:stack/gg-accel-sitewise/82df9e50-fa21-11eb-ba37-02268e8a52f9
   ```

At this point the CloudFormation stack is deployed and if the Greengrass core is running, it will have received the new deployment.

### Accelerator Cleanup

To stop and completely remove this accelerator, follow these steps:

1. From the command line where Greengrass is running (the `docker-compose` command was started), either locally on in Cloud 9, stop the Greengrass container byt entering CTRL+C and then:

   ```bash
   docker-compose down
   ```

1. With the container stopped, change to the component's CDK directory and issue the command to _destroy_ the CloudFormation stack:

   ```bash
   cd aws-iot-greengrass-accelerators/v2/sitewise/cdk
   # For Cloud9
   cdk destroy --context baseStack="gg-accel-base"
   # For locally running (replace PROFILE_NAME with one used to create stack)
   # Change baseStack if the parent stacks' default name was not used
   cdk destroy --profile PROFILE_NAME --context baseStack="gg-accel-base"
   ```

   > **NOTE:** This will only destroy the `sitewise` component resources and not the base stack. Also, since the components have already been deployed to the Greengrass core, they will continue to run unless are locally deleted via the `greengrass-cli`, or the Greengrass configuration is reset.

   At this point, all `sitewise` resources have been deleted.

1. Review any CloudWatch Logs log groups and delete these if needed.

All traces of the component including the thing group and additional AWS IoT Core policy permissions have been removed from the Greengrass core implementation.

### Frequently Asked Questions

#### Should I use this code for my production workloads?

In its current form, no. This component is not suitable for production workloads and intended to demonstrate the capabilities of Greengrass for data ingestion using OPC UA. To be production-ready would require support for additional configuration options to support various autehentication mechanisms to cater for different OPC UA endpoint configurations.