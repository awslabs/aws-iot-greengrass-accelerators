# IoTPolicy

<!--BEGIN STABILITY BANNER-->

---

![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

> All classes are under active development and subject to non-backward compatible changes or removal in any
> future version. These are not subject to the [Semantic Versioning](https://semver.org/) model.
> This means that while you may use them, you may need to update your source code when upgrading to a newer version of this package.

---

<!--END STABILITY BANNER-->

## Overview

This AWS Solutions Construct implements the creation of an [AWS IoT Core policy](https://docs.aws.amazon.com/iot/latest/developerguide/iot-policies.html), and optionally, the _certificate arn_ in which to attach this policy.

This construct returns the IoT policy arn.

TODO

- template notes
  - mappings
  - iot policy string
- docker for Lambda

Here is a minimal deployable pattern definition in Typescript assuming this code is located in same directory where being imported:

```typescript
import * as iam from "@aws-cdk/aws-iam"
import { IotThingCertPolicy } from "./IotThingCertPolicy/IotThingCertPolicy"

// IoT Core policy template
const myPolicyTemplate = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action":["iot:Publish"],
      "Resource": ["arn:aws:iot:<%= region %>:<%= account %>:topic/<% completePolicyName %>"]
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
new IotRoleAlias(scope: Construct, id: string, props: IotRoleAliasProps);
```

_Parameters_

- scope [`Construct`](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_core.Construct.html)
- id `string`
- props [`IotRoleAliasProps`](#pattern-construct-props)

## Pattern Construct Props

| **Name**         | **Type**                                                                                                     | **Description**                                                                                                      |
| :--------------- | :----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| iotRoleAliasName | `string`                                                                                                     | Base AWS IoT role alias name.                                                                                        |
| iamRoleName?     | `string`                                                                                                     | Optional base IAM Role name. Default value set to `roleAliasName`                                                    |
| iamPolicy        | [`iam.PolicyDocument`](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-iam.PolicyDocument.html) | IAM policy document to apply (inline) to the IAM role.                                                               |
| iamPolicyName?   | `string`                                                                                                     | Optional name of the default inline policy created on the IAM role. Default value set to `DefaultPolicyForRoleAlias` |

## Pattern Properties

| **Name**      | **Type**                                                                                                | **Description**                                                                               |
| :------------ | :------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| iamRoleArn    | [`iam.Role.roleArn](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-iam.Role.html#rolearn) | Returns an instance of the iam.Role.roleArn created by the construct                          |
| roleAliasName | `string`                                                                                                | Returns an instance of the roleAlias name creates by the construct for use in other resources |
| roleAliasArn  | `string`                                                                                                | Returns an instance of the roleAlias Arn creates by the construct for use in other resources  |
