import cdk = require('@aws-cdk/core');
import { CustomResourceIoTThingCertPolicy } from './cr-create-iot-thing-cert-policy/cr-iot-thing-cert-policy';
import { CustomResourceGreengrassServiceRole } from './cr-greengrass-service-role/cr-greengrass-service-role';

/**
 * A stack that sets up MyCustomResource and shows how to get an attribute from it
 */
class GreengrassStreamManagerStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);


    // Create AWS IoT Thing/Certificate/Policy as basis for Greengrass Core
    const crIoTResource = new CustomResourceIoTThingCertPolicy(this, 'CreateThingCertPolicyCustomResource', {
      functionName: id + '-CreateThingCertPolicyFunction',
      stackName: id,
    });
    new cdk.CfnOutput(this, 'CertificatePEM', {
      description: 'Certificate of Greengrass Core thing',
      value: crIoTResource.certificatePem
    });
    new cdk.CfnOutput(this, 'PrivateKeyPEM', {
      description: 'Private Key of Greengrass Core thing',
      value: crIoTResource.privateKeyPem
    });

    // Create Greengrass Service role with permissions the Core's resources should have
    new CustomResourceGreengrassServiceRole(this, "GreengrassRoleCustomResource", {
      functionName: id + '-GreengrassRoleFunction',
      stackName: id,      
      rolePolicy: {
        "Version": "2012-10-17",
        "Statement": {
            "Effect": "Allow",
            "Action": "iot:*",
            "Resource": "*",
        }
    },
    });



  }
}

// Pre-stack creation steps

// Create stack
const app = new cdk.App();
new GreengrassStreamManagerStack(app, 'gg-stream-accel');
app.synth();
