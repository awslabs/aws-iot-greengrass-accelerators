# IotThingCertPolicy module

<!--BEGIN STABILITY BANNER-->

---

![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

> All classes are under active development and subject to non-backward compatible changes or removal in any
> future version. These are not subject to the [Semantic Versioning](https://semver.org/) model.
> This means that while you may use them, you may need to update your source code when upgrading to a newer version of this package.

---

<!--END STABILITY BANNER-->

| **Language**                                                                                   | **Package**          |
| :--------------------------------------------------------------------------------------------- | -------------------- |
| ![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) Typescript | `IotThingCertPolicy` |

## Overview

This AWS Solutions Construct implements the creation of an [AWS IoT thing](https://docs.aws.amazon.com/iot/latest/developerguide/iot-thing-management.html), [AWS IoT certificate](https://docs.aws.amazon.com/iot/latest/developerguide/x509-client-certs.html), and [AWS IoT Core policy](https://docs.aws.amazon.com/iot/latest/developerguide/iot-policies.html). After creation of the resources, it also associates the _certificate_ with the _policy_ and also the _thing_. It also stores the certificate's X.509 certificate and private in [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) parameters.

This construct returns the thing arn, parameter store names, IoT data endpoint, and IoT credential provider endpoint for use in other constructs or CloudFormation outputs.

TODO

- template notes
  - mappings
  - iot policy string
- docker for Lambda

Here is a minimal deployable pattern definition in Typescript assuming this constuct's folder is located in same directory where it is being imported:

```typescript
import * as iam from "@aws-cdk/aws-iam"
import { IotThingCertPolicy } from "./IotThingCertPolicy/IotThingCertPolicy"

// IoT Core policy template
// <% thingname %> will be replaced with actual thingname created
const myPolicyTemplate = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action":["iot:Publish"],
      "Resource": ["arn:aws:iot:<%= region %>:<%= account %>:topic/<% thingname %>"]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Connect"],
      "Resource": ["arn:aws:iot:<%= region %>:<%= account %>:client/\${iot:Connection.Thing.ThingName}"]
    }
  ]
}`

// Define the IoT Core policy for use by the construct
const myThing = new IotThingCertPolicy(this, "MyThing", {
  thingName: "my-thing",
  iotPolicy: myPolicyTemplate,
  policyParameterMapping: {
    region: cdk.Fn.ref("AWS::Region"),
    account: cdk.Fn.ref("AWS::AccountId"),
  },
})
```

## Initializer

```text
new IotThingCertPolicy(scope: Construct, id: string, props: IotThingCertPolicyProps);
```

_Parameters_

- scope [`Construct`](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_core.Construct.html)
- id `string`
- props [`IotThingCertPolicyProps`](#pattern-construct-props)

## Pattern Construct Props

| **Name**                | **Type**  | **Description**                                                                                                                                                                                                                                                     |
| ----------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| thingName               | `string`  | Name of the AWS IoT Core policy to create.                                                                                                                                                                                                                          |
| iotPolicyName           | `string`  | The AWS IoT policy to be created and attached to the certificate. JSON string converted to IoT policy, lodash format for replacement.                                                                                                                               |
| iotPolicy               | `string`  | An object of parameters and values to be replaced if a Jinja template is provided. For each matching parameter in the policy template, the value will be used.                                                                                                      |
| policyParameterMapping? | `Mapping` | An object of parameters and values to be replaced if a lodash template is provided. For each matching parameter in the policy template, the value will be used. If not provided, only the `<% thingname %>` mapping will be available for the `iotPolicy` template. |
| encryptionAlgorithm?    | `string`  | Selects RSA or ECC private key and certificate generation.                                                                                                                                                                                                          | If not provided, `RSA` will be used. |
| thingName               | `string`  | Name of the AWS IoT Core policy to create.                                                                                                                                                                                                                          |

## Pattern Properties

| **Name**                          | **Type** | **Description**                                                                                                                                                                                                     |
| :-------------------------------- | :------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| certificateArn                    | `string` | Returns an instance containing the AWS IoT certificate arn.                                                                                                                                                         |
| certificatePemParameter           | `string` | Returns an instance containing the Systems Manager parameter store name of the things certificate.                                                                                                                  |
| credentialProviderEndpointAddress | `string` | Returns an instance containing the AWS IoT credential provider endpoint. Used to [authorize direct calls to other AWS services](https://docs.aws.amazon.com/iot/latest/developerguide/authorizing-direct-aws.html). |
| dataAtsEndpointAddress            | `string` | Returns an instance containing the AWS IoT Core data endpoint (ATS) for the account and region. Used by the devices to connect to the data plane.                                                                   |
| iotPolicyArn                      | `string` | Returns an instance of the AWS IoT policy attached to the certificate principal and thing.                                                                                                                          |
| privateKeySecretParameter         | `string` | Returns an instance containing the Systems Manager parameter store name of the things private key as a `SECURE_STRING` value.                                                                                       |
| thingArn                          | `string` | Returns an instance of the AWS IoT thing arn.                                                                                                                                                                       |

## CDK Deployment

This construct uses the experimental [`@aws-cdk/aws-lambda-python`](https://docs.aws.amazon.com/cdk/api/latest/docs/aws-lambda-python-readme.html) module in order to pre-install Python package dependencies. This requires the installation and use of Docker locally to operate.
