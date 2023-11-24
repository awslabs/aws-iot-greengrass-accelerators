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


from botocore.exceptions import ClientError
import comp_resource_handler
import yaml
import sys
from pathlib import Path
from botocore.config import Config
gg_config = './gg-config/gg-config.yaml'

if __name__ == '__main__':

    if comp_resource_handler.existsPreviousDeployment():
        print("Previous deployment exists. execute python compdestroy.py ")
        sys.exit(1)

    manifest = open(gg_config, "r")
    manifest_dict = yaml.safe_load(manifest.read())
    manifest.close()

    ggThingName = manifest_dict["thingName"]
    deployGroupArn = manifest_dict["thingGroupArn"]
    deployThingArn = manifest_dict["thingArn"]
    if deployGroupArn:
        print(f"Deploying to group {deployGroupArn}")
        deploymentTarget = deployGroupArn
    elif deployThingArn:
        print(f"Deploying to thing {deployThingArn}")
        deploymentTarget = deployThingArn
    else:
        print("No deployment target specified")
        sys.exit(1)
    deploymentName = ggThingName + "-deployment"

    try:
        # create componentBucket (with a random name)
        bucketName = comp_resource_handler.create_gg_bucket(ggThingName + '-')
        print(f"Created componentBucket: {bucketName}")
    except ClientError as e:
        print(f"Could not create s3 bucket: {bucketName}, {e}")
        sys.exit(1)
    
    list_to_deploy = manifest_dict["components"]
    deployment = comp_resource_handler.Deployment(deploymentName, deploymentTarget, bucketName)
    for componentName in list_to_deploy:
        component, arn = comp_resource_handler.create_component(comp_resource_handler.component_location, componentName, bucketName)
        print(f"Component created: {component}, {arn}")
        deployment.add_component(component, arn)

    resources = deployment.deploy()
    print(f"Deployment created: {resources}")