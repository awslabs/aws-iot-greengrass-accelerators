# Source Event Processing

This accelerator demonstrates a framework to subscribe, receive, and process events synchronously and asynchronously similar to AWS Lambda functions.

# Systems Manager Use Case

Provides code sames for dealing with incoming IPC events and processing then in a way similar to AWS Lambda.

# Design Pattern

The following architecture shows the process flow for deploying the accelerator.

# Folder Structure

TODO - directory when done.

```text
source_event_processing
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
