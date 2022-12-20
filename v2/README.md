# AWS IoT Greengrass Version 2 Accelerators

Each folder either contains an AWS IoT Greengrass accelerator based around common design patterns or use cases, common constructs (`cdk-constructs/`), or extra code and patterns (`extras/`). These accelerators utilize [AWS IoT Greengrass Version 2](https://docs.aws.amazon.com/greengrass/v2/developerguide/what-is-iot-greengrass.html).

All accelerators build on the [Base Implementation](base) accelerator which creates all of the required resources to run AWS IoT Greengrass locally. Additional accelerators then create an AWS CloudFormation stack using the _base_ stack's resources to create and deploy the additional components to the running Greengrass core device.

Once the _base_ has been deployed and tested, you can then select one of the other accelerators to extend the capabilities of the running Greengrass core device.

## Accelerators for AWS IoT Greengrass Version 2

- (Prerequisite) [Base Implementation](base) <--- Start here!
  - This accelerator deploys a single AWS IoT Greengrass core device as an AWS CDK constructed AWS CloudFormation stack, with all required AWS IoT, IAM, and AWS IoT Greengrass resources. It also creates a single _Hello World_ [component](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-components.html) and [deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-deployments.html) for testing purposes.
- [Sitewise Implementation](sitewise)
  - This accelerator deploys additional functionality on to the _Base Implementation_ stack to demonstrate basic AWS IoT SiteWise functionality.
- [Operating System Command Execution](os_cmd)
  - This accelerator deploys additional functionality on to the _Base Implementation_ stack to demonstrate sending an operating system command as an MQTT message from AWS IoT Core, running the command locally, and publishing back the command output to another MQTT topic in the cloud.
- [Extract, Transform, and Load - Simple Implementation](etl_simple)
  - This accelerator deploys additional functionality on to the _Base Implementation_ stack to demonstrate how to extract, transform, and load (ETL) data from a local device to the cloud. This accelerator breaks the three steps into discrete processes, decoupled by using [Interprocess Communication](https://docs.aws.amazon.com/greengrass/v2/developerguide/interprocess-communication.html).
