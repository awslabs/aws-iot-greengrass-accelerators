import cfn = require('@aws-cdk/aws-cloudformation');
import lambda = require('@aws-cdk/aws-lambda');
import iam = require('@aws-cdk/aws-iam');
import cdk = require('@aws-cdk/core');

import uuid = require('uuid/v5');

export interface CustomResourceGreengrassServiceRoleProps {
  /**
   * Resource properties used to construct the custom resource and passed as dictionary
   * to the resource as part of the "ResourceProperties". Note that the properties below
   * will have an uppercase first character and the rest of the property kept intact.
   * For example, physicalId will be passed as PhysicalId
   */
  functionName: string;
  stackName: string;
  rolePolicy: object;
  roleName?: string;
  physicalId?: string;
}

export class CustomResourceGreengrassServiceRole extends cdk.Construct {
  public readonly roleArn: string;

  constructor(scope: cdk.Construct, id: string, props: CustomResourceGreengrassServiceRoleProps) {
    super(scope, id);
    props.physicalId = props.functionName;
    // IAM role name
    props.roleName = props.stackName + "-GreengrassGroupRole"

    const resource = new cfn.CustomResource(this, 'Resource', {
      provider: cfn.CustomResourceProvider.fromLambda(new lambda.SingletonFunction(this, 'Singleton', {
        functionName: props.functionName,
        uuid: uuid(props.functionName, uuid.DNS),
        code: lambda.Code.fromAsset('cr-greengrass-service-role/cr_greengrass_service_role'),
        handler: 'index.main',
        timeout: cdk.Duration.seconds(30),
        runtime: lambda.Runtime.PYTHON_3_8,
        initialPolicy: [
          new iam.PolicyStatement({
            actions: ['iam:CreateRole', 'iam:DeleteRole', 'iam:AttachRolePolicy',
              'iam:PutRolePolicy', 'iam:ListRolePolicies', 'iam:DeleteRolePolicy', 'iam:ListAttachedRolePolicies',
              'iam:DetachRolePolicy',
            ],
            resources: ['*']
          })]
      })),
      properties: props
    });
    this.roleArn = resource.getAttString('roleArn');
  }
}

