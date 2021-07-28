# Systems Manager Accelerator

This accelerator installs and registers the AWS Systems Manager agent onto the Greengrass core device.

# Systems Manager Use Case

Provides the ability for AWS Systems Manager to manage the Greengrass core device.

# Design Pattern

The following architecture shows the process flow for deploying the accelerator.

# Folder Structure

TODO - directory when done.

```text
ssm_agent
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

# Deploying the Accelerator

## Prerequisites

The following is a list of prerequisites to deploy the accelerator:

1. Install and verify the [base] accelerator.

## Investigating the Accelerator

TODO

## Accelerator Cleanup

TODO

## Frequently Asked Questions

### Question name

Supporting details or answer

#### Resolution (optional)

Steps to resolve issue

## Implementation Notes

Technical details on how the different accelerator components run.
