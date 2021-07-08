import cdk = require("@aws-cdk/core")
import iotanalytics = require("@aws-cdk/aws-iotanalytics")

export interface IoTAnalyticsProps {
  /*
   * Properties for creating complete IoT Analytics ETL
   */
  channelName: string
  datastoreName: string
  pipelineName: string
  datasetName: string
  sqlQuery: string
  scheduledExpression: string
}

export class IoTAnalytics extends cdk.Construct {
  // Used to tie addDependsOn for other usage
  public readonly sqlDataset: iotanalytics.CfnDataset

  public readonly channelArn: string

  constructor(scope: cdk.Construct, id: string, props: IoTAnalyticsProps) {
    super(scope, id)

    const channel = new iotanalytics.CfnChannel(this, "Channel", {
      channelName: props.channelName,
    })
    // Define Arn for the channel, CloudFormation does not return this (why!!!??), so create
    this.channelArn = `arn:aws:iotanalytics:${process.env.CDK_DEFAULT_REGION}:${process.env.CDK_DEFAULT_ACCOUNT}:channel/${props.channelName}`
    const datastore = new iotanalytics.CfnDatastore(this, "Datastore", {
      datastoreName: props.datastoreName,
    })
    const pipeline = new iotanalytics.CfnPipeline(this, "Pipeline", {
      pipelineName: props.pipelineName,
      pipelineActivities: [
        {
          channel: {
            name: "ChannelActivity",
            channelName: props.channelName,
            next: "DatastoreActivity",
          },
          datastore: {
            name: "DatastoreActivity",
            datastoreName: props.datastoreName,
          },
        },
      ],
    })
    pipeline.addDependsOn(datastore)
    pipeline.addDependsOn(channel)

    this.sqlDataset = new iotanalytics.CfnDataset(this, "SqlDataset", {
      datasetName: props.datasetName,
      actions: [
        {
          actionName: "SqlAction",
          queryAction: {
            sqlQuery: props.sqlQuery,
          },
        },
      ],
      triggers: [
        {
          schedule: {
            scheduleExpression: props.scheduledExpression,
          },
        },
      ],
      retentionPeriod: {
        unlimited: false,
        numberOfDays: 30,
      },
    })
    this.sqlDataset.addDependsOn(datastore)
  }
}
