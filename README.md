# AWS IoT Greengrass Accelerators

AWS IoT Greengrass accelerators (accelerators) demonstrate common design patterns or use cases for both AWS IoT Greengrass Version 1 (V1) and also AWS IoT Greengrass Version 2 (V2).

Each subfolder under `v1/` or `/v2/` contains the accelerators. AWS IoT Greengrass V2 is the latest major version of AWS IoT Greengrass. The V1 accelerators are still applicable, but new accelerator development will focus on AWS IoT Greengrass V2.

## Accelerators for AWS IoT Greengrass V2

All of the V2 accelerators are designed to be deployed as a combination of AWS CloudFormation stacks in the cloud, and as Docker containers on your local system or through [AWS Cloud9](https://aws.amazon.com/cloud9/). This provides a consistent and quick approach to testing or investigating functionality without impacting or leaving behind unneeded artifacts. While designed for containers, the actual components can be deployed onto physical hardware, virtual machines, or Amazon Elastic Compute Cloud (Amazon EC2) instances.

The current V2 accelerators are:

- [Base Implementation](v2/base)
  - This repository deploys a single AWS IoT Greengrass core device as an AWS CDK constructed AWS CloudFormation stack, with all required AWS IoT, IAM, and AWS IoT Greengrass resources. It also creates a single _Hello World_ [component](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-components.html) and [deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-deployments.html) for testing purposes.

## Accelerators for AWS IoT Greengrass V1

- [Extract, Transform, and Load](v1/extract_transform_load)
- [Machine Learning Inference](v1/machine_learning_inference)
- [Stream Manager](v1/stream_manager) (and Docker Application Management)
