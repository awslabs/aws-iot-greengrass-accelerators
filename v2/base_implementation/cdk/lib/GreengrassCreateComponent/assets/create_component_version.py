# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import re
import sys
import json
from collections import OrderedDict
import logging as logger
from pathlib import Path
import boto3
import yaml
import yaml.constructor
from botocore.config import Config
from botocore.exceptions import ClientError

import time

logger.getLogger().setLevel(logger.INFO)
# Yaml dates can be represented as strings in Greengrass recipe files
yaml.constructor.SafeConstructor.yaml_constructors[
    "tag:yaml.org,2002:timestamp"
] = yaml.constructor.SafeConstructor.yaml_constructors["tag:yaml.org,2002:str"]

temp_environment = {
    "AWS_LAMBDA_FUNCTION_VERSION": "$LATEST",
    "AWS_LAMBDA_LOG_GROUP_NAME": "/aws/lambda/base-implementation-GreengrassCreateComponentFunct-T8vRQhoSktZJ",
    "LD_LIBRARY_PATH": "/var/lang/lib:/lib64:/usr/lib64:/var/runtime:/var/runtime/lib:/var/task:/var/task/lib:/opt/lib",
    "LAMBDA_TASK_ROOT": "/var/task",
    "AWS_LAMBDA_LOG_STREAM_NAME": "2021/07/21/[$LATEST]cd6bfd7c6ac843faa9023cf6cca0bd1b",
    "AWS_LAMBDA_RUNTIME_API": "127.0.0.1:9001",
    "AWS_EXECUTION_ENV": "AWS_Lambda_python3.8",
    "AWS_XRAY_DAEMON_ADDRESS": "169.254.79.2:2000",
    "AWS_LAMBDA_FUNCTION_NAME": "base-implementation-GreengrassCreateComponentFunct-T8vRQhoSktZJ",
    "PATH": "/var/lang/bin:/usr/local/bin:/usr/bin/:/bin:/opt/bin",
    "AWS_DEFAULT_REGION": "us-west-2",
    "PWD": "/var/task",
    "LAMBDA_RUNTIME_DIR": "/var/runtime",
    "LANG": "en_US.UTF-8",
    "AWS_LAMBDA_INITIALIZATION_TYPE": "on-demand",
    "TZ": ":UTC",
    "AWS_REGION": "us-west-2",
    "SHLVL": "0",
    "_AWS_XRAY_DAEMON_ADDRESS": "169.254.79.2",
    "_AWS_XRAY_DAEMON_PORT": "2000",
    "AWS_XRAY_CONTEXT_MISSING": "LOG_ERROR",
    "_HANDLER": "create_component_version.handler",
    "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "128",
    "PYTHONPATH": "/var/runtime",
    "_X_AMZN_TRACE_ID": "Root=1-60f899e2-70b02dda1619d879449d3b09;Parent=15e73a3a203f07f0;Sampled=0",
}
temp_create = {
    "RequestType": "Create",
    "ServiceToken": "arn:aws:lambda:us-west-2:904880203774:function:base-implementation-GreengrassCreateComponentFunct-3EgVfbmieVxm",
    "ResponseURL": "https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A904880203774%3Astack/base-implementation/e84f4eb0-ebbd-11eb-a1c8-068346d307f3%7CHelloWorldComponentGreengrassCreateComponentFunctionAAAFC343%7Cf7565cc2-251e-474d-b585-3bdcc9a94584?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20210723T135920Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIA54RCMT6SNNWC7LWJ%2F20210723%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Signature=39ced0576b65a11bed0d04c643f63e5f9bd930e0f408acab487917519c694faf",
    "StackId": "arn:aws:cloudformation:us-west-2:904880203774:stack/base-implementation/e84f4eb0-ebbd-11eb-a1c8-068346d307f3",
    "RequestId": "f7565cc2-251e-474d-b585-3bdcc9a94584",
    "LogicalResourceId": "HelloWorldComponentGreengrassCreateComponentFunctionAAAFC343",
    "ResourceType": "AWS::CloudFormation::CustomResource",
    "ResourceProperties": {
        "ServiceToken": "arn:aws:lambda:us-west-2:904880203774:function:base-implementation-GreengrassCreateComponentFunct-3EgVfbmieVxm",
        "TargetArtifactKeyName": "path1/path2/com.example.HelloWorld-1.0.0.zip",
        "ComponentZipAsset": "assets/49d082dfe7eae594edfb43694f6ddec8c648113d8a893616264702e1e1a88af6.zip",
        "ComponentPrefixPath": "",
        "RecipeFileAsset": "assets/bb47acccfffd74ba4105e22e59bf8fa1010bbbd126a68361ca2cf067001e2cf9.yaml",
        "ComponentName": "com.example.HelloWorld",
        "TargetBucket": "base-implementation-ggcomponents-904880203774-us-west-2",
        "StackName": "base-implementation",
        "AssetBucket": "cdktoolkit-stagingbucket-1v9z9sly58ptn",
        "ComponentVersion": "1.0.0",
    },
}


def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def replace(data, match, repl):
    """Replace variable with replacement text"""
    if isinstance(data, dict):
        return {k: replace(v, match, repl) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace(i, match, repl) for i in data]
    else:
        return data.replace(match, repl)
        # return repl if data == match else data


def create_resources(
    source_bucket: str,
    target_bucket: str,
    componentZip: str,
    recipeFile: str,
    component_name: str,
    component_version: str,
    artifact_file_keyname: str,
):
    """Create Greengrass component version"""
    c_greengrassv2 = get_aws_client("greengrassv2")
    c_s3 = get_aws_client("s3")
    result = {}

    # Read artifact file from s3, place in target bucket
    # Download location - can be /tmp as components will be unique
    artifact_file = str(Path("/tmp", f"{component_name}-{component_version}.zip"))
    c_s3.download_file(
        Bucket=source_bucket,
        Key=componentZip,
        Filename=artifact_file,
    )

    # read recipe file
    obj = c_s3.get_object(Bucket=source_bucket, Key=recipeFile)
    if recipeFile.lower().endswith(".json"):
        recipe = json.loads(obj["Body"].read())
    elif recipeFile.lower().endswith((".yaml", ".yml")):
        recipe = yaml.safe_load(obj["Body"].read())
    else:
        logger.error(
            "Recipe file must be in JSON or YAML format and end with .json or .yaml"
        )
        sys.exit(1)

    # transform to JSON, replace variable placeholders,
    recipe = replace(recipe, "${COMPONENT_BUCKET}", target_bucket)
    recipe = replace(recipe, "${ARTIFACT_KEY_NAME}", artifact_file_keyname)
    print(recipe)

    # upload will be to artifact_file_keyname or artifact_file if not provided
    if artifact_file_keyname:
        upload_file_name = artifact_file_keyname
    else:
        upload_file_name = f"{component_name}-{component_version}.zip"
    c_s3.upload_file(Filename=artifact_file, Bucket=target_bucket, Key=upload_file_name)

    # create component version name=version
    try:
        # First submit the request
        response = c_greengrassv2.create_component_version(
            inlineRecipe=json.dumps(recipe).encode()
        )
        component_arn = response["arn"]

        start_time = time.time()
        while time.time() - start_time < 30:
            response = c_greengrassv2.describe_component(arn=component_arn)
            if response["status"]["componentState"] == "DEPLOYABLE":
                return component_arn
            time.sleep(2)
        logger.error(
            f"Component did not become deployable, last component status returned was: {response}"
        )
        sys.exit(1)
    except c_greengrassv2.exceptions.ConflictException as e:
        logger.error(f"Componet already exists, {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Uncaught error: {e}")
        sys.exit(1)

    return result


def delete_resources(component_arn: str):
    """Delete component version"""

    c_greengrassv2 = get_aws_client("greengrassv2")
    try:
        c_greengrassv2.delete_component(arn=component_arn)
    except ClientError as e:
        logger.error(
            f"Error deleting component {component_arn}, continuing delete, {e}"
        )


def handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))
    logger.info("Environment: %s", dict(os.environ))
    props = event["ResourceProperties"]
    physical_resource_id = ""
    try:
        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            logger.info("Request CREATE")
            component_arn = create_resources(
                source_bucket=props["AssetBucket"],
                target_bucket=props["TargetBucket"],
                componentZip=props["ComponentZipAsset"],
                recipeFile=props["RecipeFileAsset"],
                component_name=props["ComponentName"],
                component_version=props["ComponentVersion"],
                artifact_file_keyname=props["TargetArtifactKeyName"],
            )

            # set response data (PascalCase key)
            response_data = {"ComponentArn": component_arn}
            ############# REPLACE
            physical_resource_id = component_arn
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            resp = delete_resources(
                component_arn=event["PhysicalResourceId"],
            )
            response_data = {}
            physical_resource_id = event["PhysicalResourceId"]
        else:
            logger.info("Should not get here in normal cases - could be REPLACE")

        output = {"PhysicalResourceId": physical_resource_id, "Data": response_data}
        logger.info("Output from Lambda: %s", json.dumps(output, indent=2))
        return output
    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":

    for env in temp_environment:
        os.environ[env] = temp_environment[env]

    # # create
    print("running CREATE")
    response = handler(temp_create, {})
    # time.sleep(2)
    # temp_event["RequestType"] = "Delete"
    # response = handler(temp_event, {})
