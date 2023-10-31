# Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at

# http://aws.amazon.com/asl/

# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

# This is to deploy Greengrass natively without automated provisioning
# it uses the environmental variable file .env in the current directory 

import shutil
import core_resource_handler
import json
import sys
import os
from pathlib import Path
import dotenv
import pyuac
import subprocess
import yaml


def clean_config(dirs_to_clean: list):
    """remove greengrass root folder, to reset greengrass state"""
    print("Cleaning greengrass ...")
    for dir in dirs_to_clean:
        path = Path(dir)
        if path.exists():
            print(f"Deleting files in {path}")
            try:
                shutil.rmtree(path)
            except PermissionError as e:
                print("Cannot clean greengrass folder, please stop Greengrass and try again (sc stop greengrass)", e)
                exit(1)

        #os.makedirs(path, 0o777)
        print(f"Directory '{dir} cleaned")


def copy_creds_to_tmp(config_yaml, source_dir):
    # copy credentials to tmp folder
    with open(config_yaml, 'r') as f:
        config = yaml.safe_load(f)
    file_dst = config['system']['rootCaPath']
    dir_dst = os.path.dirname(file_dst)
    try:
        shutil.copytree(source_dir, dir_dst, dirs_exist_ok=True)

    except Exception as e:
        print(e)
        exit(1)
    print("Credentials copied to tmp folder")
    return


if __name__ == '__main__':

    if not pyuac.isUserAdmin():
        print("The script must be executed as admin")
        exit(1)

    # if file .env does not exist in current directory stop the program
    if not os.path.isfile('.env'):
        print('.env file does not exist in current directory. Execute python deploy.py')
        exit(1)
    else:
        dotenv.load_dotenv()
    GGC_ROOT_PATH = os.getenv('GGC_ROOT_PATH')
    PROVISION = os.getenv('PROVISION')
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    COMPONENT_DEFAULT_USER = os.getenv('COMPONENT_DEFAULT_USER')
    DEPLOY_DEV_TOOLS = os.getenv('DEPLOY_DEV_TOOLS')
    INIT_CONFIG = os.getenv('INIT_CONFIG')
    THING_NAME = os.getenv("THING_NAME")
    THING_GROUP_NAME = os.getenv("THING_GROUP_NAME")
    THING_POLICY_NAME = os.getenv("THING_POLICY_NAME")
    TES_ROLE_NAME = os.getenv("TES_ROLE_NAME")
    TES_ROLE_ALIAS_NAME = os.getenv("TES_ROLE_ALIAS_NAME")
    print(GGC_ROOT_PATH)
    print(INIT_CONFIG)
    print(AWS_DEFAULT_REGION)
    print(COMPONENT_DEFAULT_USER)
    print(DEPLOY_DEV_TOOLS)
    print(THING_NAME)
    print(PROVISION)

    # check if Greengrass is already installed
    if (GGC_ROOT_PATH is None) or (INIT_CONFIG is None) or (AWS_DEFAULT_REGION is None) or (COMPONENT_DEFAULT_USER is None) or (TES_ROLE_ALIAS_NAME is None) or (THING_NAME is None):
        print("Some Environmental variables are empty, check or re-run the gg-docker-deploy.py script")
        print(os.environ)
        exit(1)

    # verify the path using getcwd()
    cwd = os.getcwd()
    # print the current directory
    print("Current working directory is:", cwd)

    clean_config([GGC_ROOT_PATH])
    print('Greengrass resources deleted')

    print("Install Greengrass")
    # certificates and private key are set to point to /tmp/certs but they are created in ./docker/volumes/certs
    copy_creds_to_tmp(INIT_CONFIG, './docker/volumes/certs')
    options = [
               "--setup-system-service","true", "--provision","false", "--deploy-dev-tools",f"{DEPLOY_DEV_TOOLS}",
               "--aws-region", f"{AWS_DEFAULT_REGION}", "--start", "false", "--tes-role-alias-name", f"{TES_ROLE_ALIAS_NAME}",
               "--tes-role-name", f"{TES_ROLE_NAME}", "--thing-name", f"{THING_NAME}",
               "--thing-group-name", f"{THING_GROUP_NAME}", "--thing-policy-name", f"{THING_POLICY_NAME}",
               "--provision", "false", "--init-config", f"{INIT_CONFIG}", "--start", "true",
               "--setup-system-service", "true",
               "--component-default-user", "ggc_user"]
    results = subprocess.call(['java', f"-Droot={GGC_ROOT_PATH}", "-Dlog.store=FILE",'-jar', 'greengrass-nucleus/lib/Greengrass.jar']+options, shell=False)
    if results:
        print("Greengrass installation failed")
        exit(1)
    loader_path = f"{GGC_ROOT_PATH}/alts/init/distro/bin/loader"
    print(loader_path)
    results = subprocess.call(['cmd.exe', loader_path], shell=False)