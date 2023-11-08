# AWS IoT Greengrass Accelerators

AWS IoT Greengrass accelerators (accelerators) demonstrate common design patterns or use cases for both AWS IoT Greengrass Version 1 (V1) and also AWS IoT Greengrass Version 2 (V2).

Each subfolder under `v1/` or `/v2/` contains the accelerators. AWS IoT Greengrass V2 is the latest major version of AWS IoT Greengrass. The V1 accelerators are still applicable, but new accelerator development will focus on AWS IoT Greengrass V2.

## Accelerators for AWS IoT Greengrass V2

All of the V2 accelerators are designed to be deployed as a combination of AWS CloudFormation stacks in the cloud, and as Docker containers on your local system or through [AWS Cloud9](https://aws.amazon.com/cloud9/). This provides a consistent and quick approach to testing or investigating functionality without impacting or leaving behind unneeded artifacts. While designed for containers, the actual components can be deployed onto physical hardware, virtual machines, or Amazon Elastic Compute Cloud (Amazon EC2) instances.

The current V2 accelerators are:

- (Prerequisite) [Base Implementation](v2/base) <--- Start here!
  - This accelerator deploys a single AWS IoT Greengrass core device as an AWS CDK constructed AWS CloudFormation stack, with all required AWS IoT, IAM, and AWS IoT Greengrass resources. It also creates a single _Hello World_ [component](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-components.html) and [deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-deployments.html) for testing purposes.
- [Operating System Command Execution](v2/os_cmd)
  - This accelerator deploys additional functionality on to the _Base Implementation_ stack to demonstrate sending an operating system command as an MQTT message from AWS IoT Core, running the command locally, and publishing back the command output to another MQTT topic in the cloud.
- [Extract, Transform, and Load  - Simple Implementation](v2/etl_simple)
  - This accelerator deploys additional functionality on to the _Base Implementation_ stack to demonstrate how to extract, transform, and load (ETL) data from a local device to the cloud. This accelerator breaks the three steps into discrete processes, decoupled by using [Interprocess Communcation](https://docs.aws.amazon.com/greengrass/v2/developerguide/interprocess-communication.html).
- [AWS IoT SiteWise Deployment](v2/aws_iot_sitewise)
  - This accelerator deploys additional functionality on to the _Base Implementation_ stack to demonstrate a basic AWS IoT SiteWise deployment. Specifically, it leverages the AWS IoT SiteWise OPC-UA collector component to collect data from a configurable OPC-UA endpoint.

## Accelerators for AWS IoT Greengrass V1

- [Extract, Transform, and Load](v1/extract_transform_load)
- [Machine Learning Inference](v1/machine_learning_inference)
- [Stream Manager](v1/stream_manager) (and Docker Application Management)


# CDK-Less AWS IoT Greengrass Version 2 Accelerators

This version of the accelerators is meant to target systems with limited capabilities where is not possible to install docker locally (for custom resource deployment). For example, windows 10 gateways, where the Linux subsystem, needed to run containers, is not present, either for limitation in the hardware or because they host a custom Windows OS version where for security reasons is not possible to run linux containers.

The accelerators consist in 5 python scripts performing:
* Resource deployment/deletion for Greengrass on docker
* components deployment/deletion
* Windows native greengrass installation

- [Instructions](no-cdk/README.md)
- [core deployment](no-cdk/gg-docker-deploy.py)
- [component framework](no-cdk/ggComponents/)
- [Windows installation](no-cdk/win-gg-install.py)
- 