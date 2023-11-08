# Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at

# http://aws.amazon.com/asl/

# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

# This script creates a deployment with the component specified in a list
# for the greengrass instance specified in 'resource/manifest.json'


import shutil
from botocore.exceptions import ClientError

import core_resource_handler
import json
import yaml
import sys
import os
from pathlib import Path
import base64
import boto3
import re
from botocore.config import Config
import logging as logger
import time
import uuid

component_location = './ggComponents/'
manifestFile = './resources/component_manifest.json'

logger.getLogger().setLevel(logger.INFO)
# Yaml dates can be represented as strings in Greengrass recipe files
# force any unquoted dates to string instead of datetime
yaml.constructor.SafeConstructor.yaml_constructors[
    "tag:yaml.org,2002:timestamp"
] = yaml.constructor.SafeConstructor.yaml_constructors["tag:yaml.org,2002:str"]

def clean_config(dirs_to_clean: list):
    """remove all docker volume files, restore to un-configured state"""
    print("Cleaning Docker volumes...")
    for dir in dirs_to_clean:
        path = Path(dir)
        if path.exists():
            print(f"Deleting files in {path}")
            shutil.rmtree(path)
        os.makedirs(path, 0o777)
        print(f"Directory '{dir} cleaned")


def makeid(length) -> str:
    return base64.b64encode(os.urandom(32)).decode('ascii')[:length]

def existsPreviousDeployment() -> bool:
    # if component_manifest doesn't exist it means no previous deployment was executed
    if not os.path.exists(manifestFile):
        return False
    else:
        return True

def create_gg_bucket(s3Prefix):
    try:
        s3_resource = boto3.resource('s3')
        session = boto3.session.Session()
        region = session.region_name
        bucket_name = ''.join([s3Prefix, str(uuid.uuid4())]).lower()
        bucket_response = s3_resource.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': region})
        logger.info(f"Created bucket {bucket_name}")
        return bucket_response.name
    except ClientError as e:
        logger.error(f"Error creating bucket {bucket_name}, {e}")
        sys.exit(1)


def emptyBucket(bucketName: str):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketName)
    bucket.objects.all().delete()
    print(f"Bucket {bucketName} emptied")

def delete_bucket(name: str):
    try:
        s3 = boto3.resource("s3")
        c_s3 = get_aws_client('s3')
        bucket = s3.Bucket(name)
        bucket.objects.all().delete()
        c_s3.delete_bucket(Bucket=name)
    except ClientError as e:
        logger.error(f"Error deleting bucket {name}, {e}.")
    return

class Deployment:
    def __init__(self, name: str, target: str, componentBucket:str):
        self.name = name
        self.targetArn = target
        self.client = boto3.client('greengrassv2')
        self.deploymentId = ''
        self.componentList = dict()
        self.componentArnList = []
        self.componentBucket = componentBucket

    def add_component(self, component:dict, arn: str):
        self.componentArnList.append(arn)
        self.componentList.update(component)

    def deploy(self):
        print("component to deploy:", self.componentList)
        print("Deployment name: ", self.name)
        print("Deployment target: ", self.targetArn)
        try:
            response = self.client.create_deployment(targetArn=self.targetArn,deploymentName=self.name,components=self.componentList)
            self.deploymentId = response['deploymentId']
            print("Deployment created")
            # write the manifest file
            self.write_manifest()

        except ClientError as e:
            print(f"Error creating deployment {self.name}: {e}")
            sys.exit(1)
        return self.name

    def write_manifest(self):
        #write the component list to manifest file
        d = dict()
        d['components'] = self.componentList
        d['componentArns'] = self.componentArnList
        d['deploymentName'] = self.name
        d['deploymentTarget'] = self.targetArn
        d['deploymentId'] = self.deploymentId
        d['componentBucket'] = self.componentBucket
        try:
            # store result in ./resources/component_manifest.json file
            manifest = open(manifestFile, "w")
            manifest.write(json.dumps(d, indent=4, sort_keys=True))
            manifest.close()
        except ClientError as e:
            logger.error(f"Error writing {manifestFile}.json, {e}")
            sys.exit(1)
        return d
    

def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),)


def get_recipe(componentLocation:str, componentName: str):
    recipeFile = f"{componentLocation}{componentName}/recipe.yaml"
    print(f"recipe file: {recipeFile}")
    with open(recipeFile, 'r') as stream:
        try:
            # Converts yaml document to python object
            recipe = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(e)
    recipeProps = dict()
    recipeProps['componentName'] = componentName
    recipeProps['componentVersion'] = recipe['ComponentVersion']
    recipeProps['artifactZipPrefix'] = f"{componentName}/{recipe['ComponentVersion']}"
    recipeProps['targetArtifactKeyName'] = f"{componentName}.zip"
    recipeProps['sourceArtifactPath'] = f"{componentLocation}/{componentName}/artifacts"
    recipeProps['sourceRecipeFile'] = recipeFile
    return recipeProps


def replace(data, match, repl):
    """Replace variable with replacement text"""
    if isinstance(data, dict):
        return {k: replace(v, match, repl) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace(i, match, repl) for i in data]
    else:
        return data.replace(match, repl)


def create_component_resources(
    source_folder: str,
    target_bucket: str,
    recipeFile: str,
    component_name: str,
    component_version: str,
    component_prefix_path: str,
    artifact_file_keyname: str,
) -> object:
    """
    Create Greengrass component version

    Copy the components artifact zip file to stack defined bucket,
    then read and replace any construct variables in recipe file
    and create component.
    """
    c_greengrassv2 = get_aws_client("greengrassv2")
    c_s3 = get_aws_client("s3")
    result = {}
    logger.info(f"Component_name -------> {component_name}")
    logger.info(f"Component Version ----> {component_version}")
    result[component_name] = {
        "componentVersion" : component_version,
        "configurationUpdate": {
            "reset": []
        }
    }
    # Read recipe file from component directory
    with open(recipeFile, 'r') as stream:
        try:
            # Converts yaml document to python object
            recipe = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(e)
            exit(1)

    # Optionally replace variable placeholders with provided values
    recipe = replace(recipe, "COMPONENT_NAME", component_name)
    recipe = replace(recipe, "COMPONENT_VERSION", component_version)
    recipe = replace(recipe, "COMPONENT_BUCKET", target_bucket)
    recipe = replace(recipe, "ARTIFACT_KEY_NAME", artifact_file_keyname)
    logger.info(f"Output recipe file is {json.dumps(recipe, indent=2)}")

    #remove the tmp folder if it exist
    shutil.rmtree('./tmp/', ignore_errors=True)
    shutil.rmtree('./tmp2/', ignore_errors=True)
    shutil.copytree(source_folder, f'./tmp2/{component_name}')

    # create a zip file from component_location + componentName
    componentZip = shutil.make_archive(base_name=f'./tmp/{component_name}', format='zip',
                                       root_dir=f'./tmp2/{component_name}/artifacts')

    # upload component zip to
    # component_prefix_path + artifact_file_keyname

    c_s3.upload_file(
        Filename=componentZip,
        Bucket=target_bucket,
        Key=f"{component_prefix_path}{artifact_file_keyname}",
    )

    # create component version name=version
    try:
        # First submit the request
        response = c_greengrassv2.create_component_version(inlineRecipe=json.dumps(recipe).encode())
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
                return result, component_arn
            time.sleep(2)
        logger.error(f"Component did not become deployable, last component status returned was: {response}")
        sys.exit(1)
    except c_greengrassv2.exceptions.ConflictException as e:
        logger.error(f"Component already exists, {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Uncaught error: {e}")
        sys.exit(1)


def create_component(component_location: str, componentName: str, bucketName: str):
    recipe = get_recipe(component_location, componentName)

    componentPrefixPath = recipe.get('artifactZipPrefix')
    if componentPrefixPath:
        if not componentPrefixPath.endswith('/'):
            componentPrefixPath += '/'

    targetArtifactKeyName = recipe.get('targetArtifactKeyName')

    if not targetArtifactKeyName:
        targetArtifactKeyName = recipe.get('componentName') + '-' + recipe.get("componentVersion") + '.zip'
    targetArtifactKeyName = re.sub('/+', '/', targetArtifactKeyName)
    print(f"Target artifact key name: {targetArtifactKeyName}")
    sourceArtifactPath = recipe.get('sourceArtifactPath')
    sourceArtifactPath = re.sub('/+', '/', sourceArtifactPath)
    print(f'source artifact path: {sourceArtifactPath}')

    source_folder = component_location + componentName

    return create_component_resources(
        source_folder=source_folder,
        target_bucket=bucketName,
        recipeFile=recipe.get('sourceRecipeFile'),
        component_name=componentName,
        component_version=recipe.get('componentVersion'),
        component_prefix_path=componentPrefixPath,
        artifact_file_keyname=targetArtifactKeyName)


def delete_component_resources(component_arn: str):
    """Delete component version"""
    c_greengrassv2 = get_aws_client("greengrassv2")
    try:
        c_greengrassv2.delete_component(arn=component_arn)
    except ClientError as e:
        logger.error(f"Error deleting component {component_arn}, continuing delete, {e}")

def write_empty_manifest(componentBucket:str):
    # write the manifest file with empty fields (except, eventually the componentBucket)
    d = dict()
    d['components'] = {}
    d['componentArns'] = [] 
    d['deploymentName'] = ""
    d['deploymentTarget'] = ""
    d['deploymentId'] = ""
    d['componentBucket'] = componentBucket
    try:
        # store result in ./resources/component_manifest.json file
        with open(manifestFile, "w") as manifest:
            manifest.write(json.dumps(dict(), indent=4, sort_keys=True))
    except ClientError as e:
        logger.error(f"Error writing {manifestFile}.json, {e}")
        sys.exit(1)
    return d

def cleanUpPreviousDeployment():
    if not existsPreviousDeployment():
        print("No previous deployment found")
        exit(0)

    manifest = open(manifestFile, "r")
    manifest_dict = json.loads(manifest.read())
    manifest.close()

    componentArns = manifest_dict["componentArns"]
    deploymentTarget = manifest_dict["deploymentTarget"]
    deployName = manifest_dict["deploymentName"]
    bucketName = manifest_dict["componentBucket"]
    deploymentId = manifest_dict["deploymentId"]

    if bucketName:        
        # delete component bucket 
        delete_bucket(bucketName)

    c_greengrassv2 = get_aws_client("greengrassv2")
    # delete all components in the manifest file
    for componentArn in componentArns:
        try:
            c_greengrassv2.delete_component(arn=componentArn)
            logger.info(f"Component {componentArn} deleted")
        except ClientError as e:
            logger.error(f"Error deleting component {componentArn}, continuing delete, {e}")

    # cancel the deployment
    try:
        c_greengrassv2.cancel_deployment(deploymentId=deploymentId)
    except ClientError as e:
        logger.warning( f"Error calling greengrassv2.cancel_deployment() for deployment id {deploymentId}, error: {e}")

    # delete deployment
    try:
        c_greengrassv2.delete_deployment(deploymentId=deploymentId)
        logger.info(f"Deployment {deployName} deleted")
    except Exception as e:
        print(f"Error deleting deployment {deployName}: {e}")
    finally:
        # delete manifest file
        os.remove(manifestFile)

