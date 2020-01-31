import cdk = require('@aws-cdk/core');
import greengrass = require('@aws-cdk/aws-greengrass');
import { CustomResourceIoTThingCertPolicy } from './cr-create-iot-thing-cert-policy/cr-iot-thing-cert-policy';
import { CustomResourceGreengrassServiceRole } from './cr-greengrass-service-role/cr-greengrass-service-role';
import { GreengrassLambdaSensorSource } from './lambda-gg-sensor-source/lambda-gg-sensor-source';
import { GreengrassLambdaStreamProducer } from './lambda-gg-stream-producer/lambda-gg-stream-producer';
import { GreengrassLambdaStreamAggregator } from './lambda-gg-stream-aggregator/lambda-gg-stream-aggregator';

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

    // Functions to be used in the Greengrass Group Deployment

    const ggLambdaSensorSource = new GreengrassLambdaSensorSource(this, "GreengrassLambdaSensorSource", {
      functionName: id + '-GreengrassLambda-SensorSource',
      stackName: id,
    });
    const ggLambdaStreamProducer = new GreengrassLambdaStreamProducer(this, "GreengrassLambdaStreamProducer", {
      functionName: id + '-GreengrassLambda-StreamProducer',
      stackName: id,
    });
    const ggLambdaStreamAggregator = new GreengrassLambdaStreamAggregator(this, "GreengrassLambdaStreamAggregator", {
      functionName: id + '-GreengrassLambda-StreamAggregator',
      stackName: id,
    });

    /*
    * This section pulls together all the Greengrass related definitions, and creates the Deployment
    */

    // Create Greengrass Lambda Function definition - All defined as process mode to support running in Docker
    //@ts-ignore
    const functionDefinition = new greengrass.CfnFunctionDefinition(this, 'FunctionDefinition', {
      name: 'GreengrassFunction',
      initialVersion: {
        functions: [
          {
            id: '1',
            functionArn: ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
            functionConfiguration: {
              encodingType: 'binary',
              // memorySize: 65536,
              pinned: true,
              timeout: 3,
              environment: {
                // Run as process (NoContainer)
                execution:{
                    isolationMode: 'NoContainer',
                    runAs: {
                      gid: 0,
                      uid: 0
                    }
                },
              }
            }
          },
          {
            id: '2',
            functionArn: ggLambdaStreamProducer.greengrassLambdaAlias.functionArn,
            functionConfiguration: {
              encodingType: 'binary',
              // memorySize: 65536,
              pinned: true,
              timeout: 3,
              environment: {
                // Run as process (NoContainer)
                execution:{
                    isolationMode: 'NoContainer',
                    runAs: {
                      gid: 0,
                      uid: 0
                    }
                },
              }
            }
          },
          {
            id: '3',
            functionArn: ggLambdaStreamAggregator.greengrassLambdaAlias.functionArn,
            functionConfiguration: {
              encodingType: 'binary',
              // memorySize: 65536,
              pinned: true,
              timeout: 3,
              environment: {
                // Run as process (NoContainer)
                execution:{
                    isolationMode: 'NoContainer',
                    runAs: {
                      gid: 0,
                      uid: 0
                    }
                },
              }
            }
          }
        ]
      }
    });

    // Greengrass Core Definition
    const coreDefinition = new greengrass.CfnCoreDefinition(this, 'CoreDefinition', {
      name: 'StreamCore',
      initialVersion: {
        cores: [
          {
            certificateArn: crIoTResource.certificateArn,
            id: '1',
            thingArn: crIoTResource.thingArn
          }
        ]
      }
    });

    // Finally combine all definitions and create the Group
    //@ts-ignore
    const greengrassGroup = new greengrass.CfnGroup(this, 'GreengrassGroup', {
      name: id.split('-').join('_'),
      initialVersion: {
        coreDefinitionVersionArn: coreDefinition.attrLatestVersionArn,
        // resourceDefinitionVersionArn: resourceDefinition.attrLatestVersionArn,
        functionDefinitionVersionArn: functionDefinition.attrLatestVersionArn
      }
    });
  }
}




// Pre-stack creation steps

// Create stack
const app = new cdk.App();
new GreengrassStreamManagerStack(app, 'gg-stream-accel');
app.synth();
