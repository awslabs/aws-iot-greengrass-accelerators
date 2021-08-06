# AWS IoT Greengrass Version 2 Accelerators

Each folder contains an AWS IoT Greengrass accelerator based around common design patterns or use cases. These accelerators utilize [AWS IoT Greengrass Version 2](https://docs.aws.amazon.com/greengrass/v2/developerguide/what-is-iot-greengrass.html). All accelerators build on the [Base Implementation](base) accelerator which creates all of the required resources to run AWS IoT Greengrass locally. Additional accelerators then create an AWS CloudFormation stack using the _base_ stack's resources to create and deploy the additional components to the running Greengrass core device.

Once the _base_ has been deployed and tested, you can then select one of the other accelerators to extend the capabilities of the running Greengrass core device.

## Accelerators for AWS IoT Greengrass Version 2

- (Prerequisite) [Base Implementation](base) <--- Start here!
  - This repository deploys a single AWS IoT Greengrass core device as an AWS CDK constructed AWS CloudFormation stack. It also creates a single [component](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-components.html) and [deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-deployments.html) for component and deployment testing.
