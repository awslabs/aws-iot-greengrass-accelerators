# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import argparse
import shutil
from pathlib import Path
from urllib import request
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser()
# parser.add_argument(
#     "--profile",
#     action="store",
#     required=True,
#     dest="profile",
#     help="Your AWS CLI profile name",
# )
parser.add_argument(
    "--clean",
    action="store_true",
    help="Clean all docker resources, remove configuration files",
)


def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def replace(data: dict, match: str, repl):
    """Replace variable with replacement text"""
    if isinstance(data, dict):
        return {k: replace(v, match, repl) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace(i, match, repl) for i in data]
    else:
        return data.replace(match, repl)


def verify_cwd():
    """Verify in docker/ directory"""

    # check for sibling level directories and ../cdk
    docker_assets_path = Path("./dockerfile-assets")
    if not os.path.exists(docker_assets_path):
        print(
            f"Could not find directory 'dockerfile-assets/, run this script from the 'docker/' directory. 'python3 config_docker.py' "
        )
        sys.exit(1)


def clean_config():
    """remove all docker volume files, restore to unconfigured state"""

    dirs_to_clean = ["./volumes/certs", "./volumes/config", "./volumes/gg_root"]
    print("Cleaning Docker volumes...")
    for dir in dirs_to_clean:
        path = Path(dir)
        if path.exists():
            shutil.rmtree(path)
        os.mkdir(path)
        print(f"Directory '{dir} cleaned")


if __name__ == "__main__":
    # Confirm profile given as parameters
    args = parser.parse_args()

    verify_cwd()
    # if --clean, clear all directories and exit
    if args.clean:
        clean_config()

# check for contents in certs/ config and /gg_root/, alert and exit

# read cdk.out for stack details or use --region and --stackname
# read stack outputs from cloud
# read cert and key to memory
# load AmazonCA1.pem to memory from cloud
# process config.yml to memory
# process docker-compose.yml to memory
# with both valid, write:
#  cert, key, rootca to volumes/certs/
#  config to volumes/config/
#  docker-compose.yml to ./
