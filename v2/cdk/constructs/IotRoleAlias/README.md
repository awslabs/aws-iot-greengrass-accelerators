# aws-apigateway-iot module

<!--BEGIN STABILITY BANNER-->

---

![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

> All classes are under active development and subject to non-backward compatible changes or removal in any
> future version. These are not subject to the [Semantic Versioning](https://semver.org/) model.
> This means that while you may use them, you may need to update your source code when upgrading to a newer version of this package.

---

<!--END STABILITY BANNER-->

## Overview

This AWS Solutions Construct implements an AWS IoT role alias used by clients that interact with the AWS IoT Core credentials provider.

This construct creates the role alias and an IAM role with the provided IAM policy. It returns the role alias name arn for use in other constructs.

Here is a minimal deployable pattern definition in Typescript assuming this code is located in same directory where being imported:

```typescript
import * as iam from "@aws-cdk/aws-iam"
import { IotRoleAlias } from "./IotRoleAlias/IotRoleAlias"

// Define the IAM policy for use by the role alias
const greengrassRoleMinimalPolicy = new iam.PolicyDocument({
  statements: [
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "iot:DescribeCertificate",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive",
        "s3:GetBucketLocation"
      ],
      resources: ["*"]
    })
  ]
})

new IotRoleAlias(this, "IoTRoleAliasPattern", {
  iotRoleAliasName: "GreengrassV2TokenExchangeRole",
  iamRoleName: "RoleAliasForGreengrassCore",
  iamPolicy: greengrassRoleMinimalPolicy
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

| **Name**      | **Type**                                                                                                 | **Description**                                                                               |
| :------------ | :------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| iamRoleArn    | [`iam.Role.roleArn`](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-iam.Role.html#rolearn) | Returns an instance of the iam.Role.roleArn created by the construct                          |
| roleAliasName | `string`                                                                                                 | Returns an instance of the roleAlias name creates by the construct for use in other resources |
| roleAliasArn  | `string`                                                                                                 | Returns an instance of the roleAlias Arn creates by the construct for use in other resources  |
