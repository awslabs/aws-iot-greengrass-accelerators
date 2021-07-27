# AWS IoT Greengrass Version 2 Accelerators

Each folder contains an AWS IoT Greengrass accelerator based around common design patterns or use cases. These accelerators utilize [AWS IoT Greengrass Version 2](https://docs.aws.amazon.com/greengrass/v2/developerguide/what-is-iot-greengrass.html). All accelerators utilize the [Base Implementation](base) accelerator which creates all of the core resources to run AWS IoT Greengrass locally, and then create an additional AWS CloudFormation stack to create and deploy the components to the running Greengrass core device.

Once the _base_ has been deployed and testing, you can then select one of the other accelerators to extend the capabilities of the running Greengrass core device.

## Accelerators for AWS IoT Greengrass Version 2

- (Prerequisite) [Base Implementation](base) <--- Start here!
  - This repository deploys a single AWS IoT Greengrass core device as an AWS CDK constructed AWS CloudFormation stack. It also creates a single [component](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-components.html) and [deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-deployments.html) for component and deployment testing.
