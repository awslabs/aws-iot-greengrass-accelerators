import cdk = require("@aws-cdk/core")
import greengrass = require("@aws-cdk/aws-greengrass")
import s3 = require("@aws-cdk/aws-s3")
import kinesis = require("@aws-cdk/aws-kinesis")
import { IoTAnalytics } from "./iot-analytics/iot-analytics"
import { CustomResourceIoTThingCertPolicy } from "./cr-create-iot-thing-cert-policy/cr-iot-thing-cert-policy"
import { CustomResourceGreengrassServiceRole } from "./cr-greengrass-service-role/cr-greengrass-service-role"
import { CustomResourceGreengrassManageDeployments } from "./cr-greengrass-manage-deployments/cr-greengrass-manage-deployments"
import { CustomResourceS3DeleteObjects } from "./cr-s3-delete-objects/cr-s3-delete-objects"
import { GreengrassLambdaSensorSource } from "./lambda-gg-sensor-source/lambda-gg-sensor-source"
import { GreengrassLambdaStreamProducer } from "./lambda-gg-stream-producer/lambda-gg-stream-producer"
import { GreengrassLambdaStreamAggregator } from "./lambda-gg-stream-aggregator/lambda-gg-stream-aggregator"
import { RemovalPolicy } from "@aws-cdk/core"

/**
 * A stack that sets up a complete Greengrass environment
 */
class GreengrassStreamManagerStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // S3 bucket to hold the docker-compose.yml file
    // This is created with a common bucket name and the account number to make unique
    const s3Bucket = new s3.Bucket(this, "S3SourceBucket", {
      bucketName: id.toLowerCase() + "-greengrass-source-" + props?.env?.region,
      versioned: false,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: RemovalPolicy.DESTROY,
    })
    new cdk.CfnOutput(this, "GreengrassSourceBucket", {
      description: "S3 bucket used by Greengrass for Docker compose files ",
      value: s3Bucket.bucketName,
    })
    // Associate custom resource to clean out bucket during delete
    const crS3DeleteObjects = new CustomResourceS3DeleteObjects(
      this,
      "DeleteS3Objects",
      {
        functionName: id + "-S3DeleteObjects",
        stackName: id,
        bucketName: s3Bucket.bucketName,
      }
    )
    crS3DeleteObjects.node.addDependency(s3Bucket)

    /*
     * Target resources for the Greengrass Stream Manager
     */

    // Create IoT Analytics resources for low priority / non-aggregated data
    var channelName = `${id.split("-").join("_")}_sensordata`
    const iotAnalyticsData = new IoTAnalytics(this, "IotAnalyticsStack", {
      channelName: channelName,
      datastoreName: `${id.split("-").join("_")}_sensordata_datastore`,
      pipelineName: `${id.split("-").join("_")}_sensordata_pipeline`,
      datasetName: `${id.split("-").join("_")}_sensordata_dataset`,
      sqlQuery: `select * from ${channelName}_datastore where __dt >= current_date - interval '1' day and from_unixtime(timestamp) > now() - interval '15' minute`,
      scheduledExpression: "cron(0/5 * * * ? *)",
    })

    // Kinesis Data Stream for 5 second average data
    const kinesisStream = new kinesis.Stream(this, "KinesisStream", {
      streamName: "AggregateData",
    })

    // Create AWS IoT Thing/Certificate/Policy as basis for Greengrass Core
    const crIoTResource = new CustomResourceIoTThingCertPolicy(
      this,
      "CreateThingCertPolicyCustomResource",
      {
        functionName: id + "-CreateThingCertPolicyFunction",
        stackName: id,
      }
    )
    new cdk.CfnOutput(this, "CertificatePEM", {
      description: "Certificate of Greengrass Core thing",
      value: crIoTResource.certificatePem,
    })
    new cdk.CfnOutput(this, "PrivateKeyPEM", {
      description: "Private Key of Greengrass Core thing",
      value: crIoTResource.privateKeyPem,
    })
    new cdk.CfnOutput(this, "ThingArn", {
      description: "Arn for IoT thing",
      value: crIoTResource.thingArn,
    })
    new cdk.CfnOutput(this, "EndpointDataAts", {
      description: "IoT data endpoint",
      value: crIoTResource.endpointDataAts,
    })

    // Create Greengrass Service role with permissions the Core's resources should have
    const ggServiceRole = new CustomResourceGreengrassServiceRole(
      this,
      "GreengrassRoleCustomResource",
      {
        functionName: id + "-GreengrassRoleFunction",
        stackName: id,
        rolePolicy: {
          Version: "2012-10-17",
          Statement: [
            // Allow All IoT functions
            {
              Effect: "Allow",
              Action: "iot:*",
              Resource: "*",
            },
            // Allow Greengrass Core to log to CloudWatch Logs
            {
              Effect: "Allow",
              Action: [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
              ],
              Resource: ["arn:aws:logs:*:*:*"],
            },
            // Allow access to the AWS IoT Analytics channel for ingest
            {
              Effect: "Allow",
              Action: "iotanalytics:*",
              Resource: iotAnalyticsData.channelArn,
            },
            // Allow access to Kinesis data stream for ingest
            {
              Effect: "Allow",
              Action: "kinesis:ListStreams",
              Resource: "*",
            },
            {
              Effect: "Allow",
              Action: "kinesis:*",
              Resource: kinesisStream.streamArn,
            },
          ],
        },
      }
    )

    // Functions to be used in the Greengrass Group Deployment
    const ggLambdaSensorSource = new GreengrassLambdaSensorSource(
      this,
      "GreengrassLambdaSensorSource",
      {
        functionName: id + "-GreengrassLambda-SensorSource",
        stackName: id,
      }
    )
    const ggLambdaStreamProducer = new GreengrassLambdaStreamProducer(
      this,
      "GreengrassLambdaStreamProducer",
      {
        functionName: id + "-GreengrassLambda-StreamProducer",
        stackName: id,
      }
    )
    const ggLambdaStreamAggregator = new GreengrassLambdaStreamAggregator(
      this,
      "GreengrassLambdaStreamAggregator",
      {
        functionName: id + "-GreengrassLambda-StreamAggregator",
        stackName: id,
      }
    )

    /*
     * This section pulls together all the Greengrass related definitions, and creates the Deployment
     */

    // Greengrass Core Definition
    const coreDefinition = new greengrass.CfnCoreDefinition(
      this,
      "CoreDefinition",
      {
        name: "StreamCore",
        initialVersion: {
          cores: [
            {
              certificateArn: crIoTResource.certificateArn,
              id: "1",
              thingArn: crIoTResource.thingArn,
            },
          ],
        },
      }
    )

    // Create Greengrass Lambda Function definition - Placeholder for group deployment, contents
    // come from the function definition version
    const functionDefinition = new greengrass.CfnFunctionDefinition(
      this,
      "FunctionDefinition",
      {
        name: "GreengrassFunction",
      }
    )
    // Create the Lambda function definition version from the definition above
    // This is required in order to pass the defaultConfig
    // @ts-ignore
    const functionDefinitionVersion =
      new greengrass.CfnFunctionDefinitionVersion(
        this,
        "FunctionDefinitionVersion",
        {
          functionDefinitionId: functionDefinition.attrId,
          defaultConfig: {
            execution: {
              // All functions run as processes since the deployment is targeted for container operation
              isolationMode: "NoContainer",
            },
          },
          functions: [
            {
              // This enables the Stream Manager feature in Greengrass (core component such as Local Shadow)
              id: "1",
              functionArn: "arn:aws:lambda:::function:GGStreamManager:1",
              functionConfiguration: {
                encodingType: "binary",
                pinned: true,
                timeout: 3,
                // Uncomment if other local processes require access to Stream Manager on the same host (0.0.0.0)
                // environment: {
                //     variables: {
                //         "STREAM_MANAGER_AUTHENTICATE_CLIENT": "false"
                //     }
                // }
              },
            },
            {
              id: "2",
              functionArn:
                ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
              functionConfiguration: {
                encodingType: "binary",
                pinned: true,
                timeout: 3,
                environment: {},
              },
            },
            {
              id: "3",
              functionArn:
                ggLambdaStreamProducer.greengrassLambdaAlias.functionArn,
              functionConfiguration: {
                encodingType: "binary",
                timeout: 3,
                environment: {
                  variables: {
                    STREAM_MANAGER_CHANNEL: channelName,
                  },
                },
              },
            },
            {
              id: "4",
              functionArn:
                ggLambdaStreamAggregator.greengrassLambdaAlias.functionArn,
              functionConfiguration: {
                encodingType: "binary",
                timeout: 3,
                pinned: true,
                environment: {
                  variables: {
                    LOCAL_DATA_STREAM: "LocalDataStream",
                    KINESIS_DATA_STREAM: kinesisStream.streamName,
                  },
                },
              },
            },
          ],
        }
      )

    // Connectors to be deployed
    const connectorDefinition = new greengrass.CfnConnectorDefinition(
      this,
      "ConnectorDefinition",
      {
        name: "ConnectorDefinition",
        initialVersion: {
          connectors: [
            {
              connectorArn:
                "arn:aws:greengrass:" +
                this.region +
                "::/connectors/DockerApplicationDeployment/versions/7",
              id: "1",
              parameters: {
                DockerComposeFileS3Bucket: s3Bucket.bucketName,
                DockerComposeFileS3Key: "docker-compose.yml",
                DockerComposeFileDestinationPath: "/opt",
              },
            },
          ],
        },
      }
    )

    const subscriptionDefinition = new greengrass.CfnSubscriptionDefinition(
      this,
      "SubscriptionDefinition",
      {
        name: "SubscriptionsDefinition",
        initialVersion: {
          subscriptions: [
            {
              // Simulated sensor data published on topic 'sensor_data' and received by the producer Lambda
              id: "1",
              source: ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
              subject: "sensor_data",
              target: ggLambdaStreamProducer.greengrassLambdaAlias.functionArn,
            },
            // {
            //   // Placeholder to add additional subscriptions - example
            //   id: '2',
            //   source: ggLambdaSensorSource.greengrassLambdaAlias.functionArn,
            //   subject: 'another_topic',
            //   target: ggLambdaStreamProducer.greengrassLambdaAlias.functionArn
            // },
          ],
        },
      }
    )

    const loggerDefinition = new greengrass.CfnLoggerDefinition(
      this,
      "LoggerDefinition",
      {
        name: "LoggerDefinition",
        initialVersion: {
          loggers: [
            // Setup logging of system and lambda locally and cloud
            {
              id: "1",
              component: "GreengrassSystem",
              level: "INFO",
              type: "FileSystem",
              space: 1024,
            },
            {
              id: "2",
              component: "Lambda",
              level: "INFO",
              type: "FileSystem",
              space: 1024,
            },
            {
              id: "3",
              component: "GreengrassSystem",
              level: "WARN",
              type: "AWSCloudWatch",
            },
            {
              id: "4",
              component: "Lambda",
              level: "WARN",
              type: "AWSCloudWatch",
            },
          ],
        },
      }
    )

    // Create the Greengrass group, and then associate the GroupVersion w/ resources
    const greengrassGroup = new greengrass.CfnGroup(this, "GreengrassGroup", {
      name: id.split("-").join("_"),
      roleArn: ggServiceRole.roleArn,
    })
    greengrassGroup.addDependsOn(iotAnalyticsData.sqlDataset)
    const greengrassGroupVersion = new greengrass.CfnGroupVersion(
      this,
      "GreengrassGroupVersion",
      {
        groupId: greengrassGroup.ref,
        coreDefinitionVersionArn: coreDefinition.attrLatestVersionArn,
        subscriptionDefinitionVersionArn:
          subscriptionDefinition.attrLatestVersionArn,
        connectorDefinitionVersionArn: connectorDefinition.attrLatestVersionArn,
        loggerDefinitionVersionArn: loggerDefinition.attrLatestVersionArn,
        // resourceDefinitionVersionArn: resourceDefinition.attrLatestVersionArn,
        functionDefinitionVersionArn: functionDefinition.attrLatestVersionArn,
      }
    )

    // Attach a custom resource to the Greengrass group to do a deployment reset before attempting to delete the group
    // Create Greengrass Service role with permissions the Core's resources should have
    // NOTE: Add a dependency to the Group's GroupVersion if using that for resource management,
    // otherwise addDependency to the Group itself if using the initialVersion
    const ggResetDeployment = new CustomResourceGreengrassManageDeployments(
      this,
      "GreengrassManageDeploymentsResource",
      {
        functionName: id + "-GreengrassManageDeploymentsFunction",
        stackName: id,
        greengrassGroupName: greengrassGroup.attrName,
        greengrassGroupId: greengrassGroup.ref,
        // Optional - needed if using GroupVersion instead of InitialVersion for the Group
        greengrassGroupVersionId: greengrassGroupVersion.ref,
      }
    )
    ggResetDeployment.node.addDependency(greengrassGroupVersion)
  }
}

// Create stack
const app = new cdk.App()
new GreengrassStreamManagerStack(app, "greengrass-stream-mgr-accel", {
  env: {
    account: process.env.CDK_DEPLOY_ACCOUNT || process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEPLOY_REGION || process.env.CDK_DEFAULT_REGION,
  },
})
app.synth()
