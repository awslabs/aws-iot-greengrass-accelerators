import cfn = require('@aws-cdk/aws-cloudformation');
import lambda = require('@aws-cdk/aws-lambda');
import iam = require('@aws-cdk/aws-iam');
import cdk = require('@aws-cdk/core');

import uuid = require('uuid/v5');

export interface CustomResourceIoTThingCertPolicyProps {
  /**
   * Resource properties used to construct the custom resource and passed as dictionary
   * to the resource as part of the "ResourceProperties". Note that the properties below
   * will have an uppercase first character and the rest of the property kept intact.
   * For example, physicalId will be passed as PhysicalId
   */
  functionName: string;
  stackName: string;
  physicalId?: string;
  greengrassCoreName?: string;
}

export class CustomResourceIoTThingCertPolicy extends cdk.Construct {
  public readonly certificatePem: string;
  public readonly privateKeyPem: string;
  public readonly certificateArn: string;
  public readonly thingArn: string;
  public readonly endpointDataAts: string;

  constructor(scope: cdk.Construct, id: string, props: CustomResourceIoTThingCertPolicyProps) {
    super(scope, id);
    props.physicalId = props.functionName;
    // Core name is change to all lower-case and adding _Core designation to end
    props.greengrassCoreName = props.stackName.split("-").join("_") + "_Core"

    const resource = new cfn.CustomResource(this, 'Resource', {
      provider: cfn.CustomResourceProvider.fromLambda(new lambda.SingletonFunction(this, 'Singleton', {
        functionName: props.functionName,
        uuid: uuid(props.functionName, uuid.DNS),
        code: lambda.Code.fromAsset('cr-create-iot-thing-cert-policy/cr_iot_thing_cert_policy'),
        handler: 'index.main',
        timeout: cdk.Duration.seconds(30),
        runtime: lambda.Runtime.PYTHON_3_8,
        initialPolicy: [
          new iam.PolicyStatement({actions: ['iot:*'], resources: ['*']})]
      })),
      properties: props
    });
    // Set resource return values for use by cdk.cfnOutput
    this.certificatePem = resource.getAttString('certificatePem');
    this.privateKeyPem = resource.getAttString('privateKeyPem');
    this.thingArn = resource.getAttString('thingArn');
    this.certificateArn = resource.getAttString('certificateArn');
    this.endpointDataAts = resource.getAttString('endpointDataAts')
  }
}

