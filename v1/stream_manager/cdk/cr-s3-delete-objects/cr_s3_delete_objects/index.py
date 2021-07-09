"""
CloudFormation custom resource to delete all objects in S3 bucket defined in
the ResourceProperties->BucketName. To use, ensure there is a "DependsOn" to
the referenced bucket on the custom resource.
"""

__copyright__ = (
    "Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved."
)
__license__ = "MIT-0"

def main(event, context):
    import os
    import logging as log
    import boto3
    from botocore.exceptions import ClientError
    import cfnresponse

    log.getLogger().setLevel(log.INFO)

    # NOTE: All ResourceProperties passed will uppercase the first letter
    #       of the property and leave the rest of the case intact.

    physical_id = event["ResourceProperties"]["PhysicalId"]
    cfn_response = cfnresponse.SUCCESS

    try:
        log.info("Input event: %s", event)

        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested")
        elif event["RequestType"] == "Create":
            # Operations to perform during Create, then return attributes
            attributes = {"Response": "S3DeleteObjects CREATE performed, no actions taken"}
        elif event["RequestType"] == "Update":
            # Operations to perform during Update, then return attributes
            attributes = {"Response": "S3DeleteObjects UPDATE performed, no actions taken"}
        else:
            # Operations to perform during Delete, then return attributes
            s3 = boto3.resource("s3")
            bucket = s3.Bucket(event["ResourceProperties"]["BucketName"])
            bucket.objects.all().delete()
            attributes = {"Response": "S3DeleteObjects DELETE performed, all S3 objects in referenced bucket deleted"}
        cfnresponse.send(event, context, cfnresponse.SUCCESS, attributes, physical_id)

    except Exception as e:
        log.exception(e)
        # cfnresponse's error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
