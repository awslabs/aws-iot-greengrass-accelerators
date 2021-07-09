import os
import sys
import json
import logging
import cfnresponse
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('sagemaker')

def handler(event, context):
    responseData = {}
    try:
        logger.info("Received event: {}".format(json.dumps(event)))
        result = cfnresponse.FAILED

        if event["RequestType"] == "Delete":
            result = cfnresponse.SUCCESS
        elif event["RequestType"] == "Update" or event["RequestType"] == "Create":
            training_job_name_contains = event["ResourceProperties"].get("TrainingJobNameContains")
            if training_job_name_contains:
                logger.info("training_job_name_contains: %s" % training_job_name_contains)
                jobs = client.list_training_jobs(
                    SortBy = 'CreationTime',
                    NameContains = training_job_name_contains,
                    MaxResults = 1,
                    StatusEquals = 'Completed'
                )
                if jobs.get("TrainingJobSummaries") and len(jobs["TrainingJobSummaries"]) > 0:
                    training_job = jobs["TrainingJobSummaries"][0]["TrainingJobArn"]
                    responseData["SageMakerJobArn"] = training_job
                else:
                    logger.error("No training job found for name {} found".format(training_job_name_contains) )
                result = cfnresponse.SUCCESS
            else:
                logger.error("No training job name found")
    except ClientError as e:
        logger.error("Error: %s" % e)
        result = cfnresponse.FAILED
    logger.info(
        "Returning response of: %s, with result of: %s" % (result, responseData)
    )
    sys.stdout.flush()
    cfnresponse.send(event, context, result, responseData)
