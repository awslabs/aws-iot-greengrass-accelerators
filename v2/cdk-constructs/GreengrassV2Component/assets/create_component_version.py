# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import time
import logging as logger
from pathlib import Path
import boto3
import yaml
import yaml.constructor
from botocore.config import Config
from botocore.exceptions import ClientError


logger.getLogger().setLevel(logger.INFO)
# Yaml dates can be represented as strings in Greengrass recipe files
# force any unquoted dates to string instead of datetime
yaml.constructor.SafeConstructor.yaml_constructors[
    "tag:yaml.org,2002:timestamp"
] = yaml.constructor.SafeConstructor.yaml_constructors["tag:yaml.org,2002:str"]


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
        return str(data).replace(match, repl)


def create_resources(
    source_bucket: str,
    target_bucket: str,
    componentZip: str,
    recipeFile: str,
    component_name: str,
    component_version: str,
    component_prefix_path: str,
    artifact_file_keyname: str,
):
    """
    Create Greengrass component version

    Copy the components artifact zip file to stack defined bucket,
    then read and replace any construct variables in recipe file
    and create component.
    """
    c_greengrassv2 = get_aws_client("greengrassv2")
    c_s3 = get_aws_client("s3")

    # Read artifact file from CDK asset staging bucket, place in target bucket
    # /tmp instead of tempfile as Lambda provides that, components will be unique
    # if function is used for multiple component resources
    artifact_file = str(Path("/tmp", artifact_file_keyname))
    c_s3.download_file(
        Bucket=source_bucket,
        Key=componentZip,
        Filename=artifact_file,
    )

    # read recipe file from CDK asset staging bucket and convert to dict
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

    # Optionally replace variable placeholders with provided values
    recipe = replace(recipe, "COMPONENT_NAME", component_name)
    recipe = replace(recipe, "COMPONENT_VERSION", component_version)
    recipe = replace(recipe, "COMPONENT_BUCKET", target_bucket)
    recipe = replace(recipe, "ARTIFACT_KEY_NAME", artifact_file_keyname)
    logger.info(f"Output recipe file is {json.dumps(recipe, indent=2)}")

    # upload will be constructed file name of:
    # component_prefix_path + artifact_file_keyname
    # ex: path1/path2/foo.zip
    c_s3.upload_file(
        Filename=artifact_file,
        Bucket=target_bucket,
        Key=f"{component_prefix_path}{artifact_file_keyname}",
    )

    # create component version name=version
    try:
        # First submit the request
        response = c_greengrassv2.create_component_version(
            inlineRecipe=json.dumps(recipe).encode()
        )
        component_arn = response["arn"]

        # Wait for the component to go into a DEPLOYABLE state
        # This normally happens immediately but may take additional time
        # to complete
        start_time = time.time()
        while time.time() - start_time < 30:
            response = c_greengrassv2.describe_component(arn=component_arn)
            if response["status"]["componentState"] == "DEPLOYABLE":
                # Component registered, return the Arn as resource id so DELETE
                # has it for cancelling
                return component_arn
            time.sleep(2)
        logger.error(
            f"Component did not become deployable, last component status returned was: {response}"
        )
        sys.exit(1)
    except c_greengrassv2.exceptions.ConflictException as e:
        logger.error(f"Component already exists, {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Uncaught error: {e}")
        sys.exit(1)


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
                component_prefix_path=props["ComponentPrefixPath"],
                artifact_file_keyname=props["TargetArtifactKeyName"],
            )
            # set response data (PascalCase key) back to construct
            response_data = {"ComponentArn": component_arn}
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
        sys.exit(1)


if __name__ == "__main__":
    #### Uncomment for local testing
    # 1. deploy stack, and from CloudWatch log
    # 2. copy environment output, remove AWS access key, secret, and session token
    #    and create temp_environment dict with the output
    # 3. Create temp_create dict with output of Event
    # 4. Optionally do the same for a DELETE event too

    # for env in temp_environment:
    #     os.environ[env] = temp_environment[env]

    # # create
    # print("running CREATE")
    # response = handler(temp_create, {})
    pass
