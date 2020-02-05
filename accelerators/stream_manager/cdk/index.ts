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
    new cdk.CfnOutput(this, 'ThingArn', {
      description: 'Arn for IoT thing',
      value: crIoTResource.thingArn
    });
    new cdk.CfnOutput(this, 'EndpointDataAts', {
      description: 'IoT data endpoint',
      value: crIoTResource.endpointDataAts
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

    // Create Greengrass Lambda Function definition - Placeholder for group deployment, contents
    // come from the function definition version
    const functionDefinition = new greengrass.CfnFunctionDefinition(this, 'FunctionDefinition', {
      name: 'GreengrassFunction'
    });
    // Create the Lambda function definition version from the definition above
    //@ts-ignore
    const functionDefinitionVersion = new greengrass.CfnFunctionDefinitionVersion(this, 'FunctionDefinitionVersion', {
      functionDefinitionId: functionDefinition.attrId,
      defaultConfig: {
        execution: {
          isolationMode: "NoContainer",
          runAs: {
            gid: 0,
            uid: 0
          }
        }
      },
      functions: [
        {
          id: '1',
          functionArn: "arn:aws:lambda:::function:GGStreamManager:1",
          functionConfiguration: {
            encodingType: 'binary',
            // memorySize: 65536,
            pinned: true,
            timeout: 3,
          }
        },
        {
          id: '2',
          functionArn: ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
          functionConfiguration: {
            encodingType: 'binary',
            // memorySize: 65536,
            pinned: true,
            timeout: 3,
            environment: {
              // Run as process (NoContainer)
              execution: {
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
          functionArn: ggLambdaStreamProducer.greengrassLambdaAlias.functionArn,
          functionConfiguration: {
            encodingType: 'binary',
            // memorySize: 65536,
            pinned: true,
            timeout: 3,
            environment: {
              // Run as process (NoContainer)
              execution: {
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
          id: '4',
          functionArn: ggLambdaStreamAggregator.greengrassLambdaAlias.functionArn,
          functionConfiguration: {
            encodingType: 'binary',
            // memorySize: 65536,
            pinned: true,
            timeout: 3,
            environment: {
              // Run as process (NoContainer)
              execution: {
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
    })


    //@ts-ignore
    const subscriptionDefinition = new greengrass.CfnSubscriptionDefinition(this, 'SubscriptionDefinition', {
      name: 'SubscriptionsDefinition',
      initialVersion: {
        subscriptions: [
          {
            // Simulated sensor data published on topic 'sensor_data' and received by the producer Lambda
            id: '1',
            source: ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
            subject: 'sensor_data',
            target: ggLambdaStreamProducer.greengrassLambdaAlias.functionArn
          },
          // {
          //   // Simulated sensor data published on topic 'sensor_data' and received by the producer Lambda
          //   id: '2',
          //   source: ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
          //   subject: 'sensor_data',
          //   target: ggLambdaStreamProducer.greengrassLambdaAlias.functionArn
          // },

        ]
      } 

    })

    // Finally combine all definitions and create the Group
    //@ts-ignore
    const greengrassGroup = new greengrass.CfnGroup(this, 'GreengrassGroup', {
      name: id.split('-').join('_'),
      initialVersion: {
        coreDefinitionVersionArn: coreDefinition.attrLatestVersionArn,
        subscriptionDefinitionVersionArn: subscriptionDefinition.attrLatestVersionArn,
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