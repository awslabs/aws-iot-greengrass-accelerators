# AWS IoT Greengrass Accelerators

AWS IoT Greengrass accelerators (accelerators) demonstrate common design patterns or use cases for both AWS IoT Greengrass Version 1 and also AWS IoT Greengrass Version 2.

Each folder contains an AWS IoT Greengrass accelerator based around common design patterns or use cases. AWS IoT Greengrass Version 2 is the latest major version of AWS IoT Greengrass. The version 1 accelerators are still applicable, but new accelerator development will focus on AWS IoT Greengrass Version 2.

## Accelerators for AWS IoT Greengrass Version 2

- [Base Implementation](v2/base-implementation)
  - This repository deploys a single AWS IoT Greengrass core device as an AWS CDK constructed AWS CloudFormation stack. It also creates a single [component](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-components.html) and [deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-deployments.html) for testing purposes.

## Accelerators for AWS IoT Greengrass Version 1

- [Extract, Transform, and Load](v1/extract_transform_load)
- [Machine Learning Inference](v1/machine_learning_inference)
- [Stream Manager](v1/stream_manager) (and Docker Application Management)
