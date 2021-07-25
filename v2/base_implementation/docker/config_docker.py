# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import argparse
import shutil
import glob
import json
import urllib
import re
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ProfileNotFound

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--profile", help="Your AWS CLI profile name")
group.add_argument(
    "--clean", help="Clear all docker configuration files from volumes directories"
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
    docker_assets_path = Path("./volumes")
    if not os.path.exists(docker_assets_path):
        print(
            f"Could not find directory './volumes/, run this script from the 'docker/' directory. 'python3 config_docker.py' "
        )
        sys.exit(1)


def clean_config(dirs_to_clean: list):
    """remove all docker volume files, restore to unconfigured state"""

    print("Cleaning Docker volumes...")
    for dir in dirs_to_clean:
        path = Path(dir)
        if path.exists():
            shutil.rmtree(path)
        os.mkdir(path)
        print(f"Directory '{dir} cleaned")


def check_for_config(dirs_to_check: list, config_files: list):
    """
    Verify target directories are empty of non dot files, and that
    config files exist
    """

    print("Verifying docker volume directories empty before creating configurations")
    for dir in dirs_to_check:
        path = Path(dir)
        files = glob.glob(f"{path}/[!.]*")
        if files:
            print(
                f"Files found in '{path}', not overwriting. Run with --clean to create new configurations. Files found: {files}"
            )
            sys.exit(1)
    print("All configuration directories empty, continuing")

    for file in config_files:
        path = Path(file)
        if not file:
            print(
                f"File {file} not found. This file must exist for creating configuration files."
            )
            sys.exit(1)
    print("All configuration file templates found, continuing.")
    return


def read_manifest():
    """Read the manifest file to get the stackname

    As of cdk 1.13.1, the stackname can be found in the manifest file
    as an artifact object with a type of aws:cloudformation:stack

    """
    manifest_file = Path("../cdk/cdk.out/manifest.json")
    if manifest_file.is_file():
        with open(manifest_file) as f:
            manifest = f.read()
    else:
        print(
            "manifest.json not found in cdk.out directory. Has the stack been deployed?"
        )
        sys.exit(1)

    try:
        manifest = json.loads(manifest)
    except ValueError as e:
        print(f"Invalid format of {manifest_file}, error: {e}")
        sys.exit(1)
    # Return the stack name, account, and region
    for i in manifest["artifacts"]:
        if manifest["artifacts"][i]["type"] == "aws:cloudformation:stack":
            return {
                "stackname": i,
                "account": manifest["artifacts"][i]["environment"].split("/")[2],
                "region": manifest["artifacts"][i]["environment"].split("/")[-1],
            }


def read_parameter(
    parameter: str, session: boto3.Session, with_decryption: bool = False
):
    """Read contents of certificate from Systems Manager Parameter Store"""

    ssm = session.client("ssm")
    try:
        response = ssm.get_parameter(Name=parameter, WithDecryption=with_decryption)
    except ClientError as e:
        print(f"Error calling ssm.get_parameter() for parameter {parameter}, {e}")
    except Exception as e:
        print(f"Uncaught error, {e}")
    return response["Parameter"]["Value"]


def replace_variables(file: str, map: dict):
    """
    Replace ${TOKEN} from file with key/values in map
    """

    with open(Path(file), "r") as f:
        template = f.read()
    for k in map:
        template = re.sub(fr"\${{{k}}}", map[k], template)
    return template


if __name__ == "__main__":
    # Confirm profile given as parameters
    args = parser.parse_args()
    docker_config_directories = [
        "./volumes/certs",
        "./volumes/config",
        "./volumes/gg_root",
    ]
    template_files = ["./templates/config.yaml", "./templates/docker-compose.yaml"]
    config_values = {}

    verify_cwd()
    # if --clean, clear all directories and exit
    if args.clean:
        clean_config(docker_config_directories)

    # check for contents in certs/ config and /gg_root/, alert and exit
    check_for_config(
        dirs_to_check=docker_config_directories, config_files=template_files
    )

    # read cdk.out for stack details or use --region and --stackname
    stackname_manifest = read_manifest()
    stackname = stackname_manifest["stackname"]
    region = stackname_manifest["region"]

    # read and populate stack outputs from cloud
    try:
        session = boto3.Session(profile_name=args.profile, region_name=region)
        cloudformation = session.resource("cloudformation")
        stack = cloudformation.Stack(stackname)
        stack.load()
    except ProfileNotFound as e:
        print(f"The AWS config profile ({args.profile}) could not be found.")
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)
    # Set values for template
    for output in stack.outputs:
        if output["OutputKey"] == "CredentialProviderEndpointAddress":
            config_values["CREDENTIAL_PROVIDER_ENDPOINT"] = output["OutputValue"]
        elif output["OutputKey"] == "DataAtsEndpointAddress":
            config_values["DATA_ATS_ENDPOINT"] = output["OutputValue"]
        elif output["OutputKey"] == "IotRoleAliasName":
            config_values["IOT_ROLE_ALIAS"] = output["OutputValue"]
        elif output["OutputKey"] == "ThingArn":
            config_values["THING_NAME"] = output["OutputValue"].split("/")[-1]
        elif output["OutputKey"] == "CertificatePemParameter":
            certificate_pem = read_parameter(
                parameter=output["OutputValue"], session=session
            )
        elif output["OutputKey"] == "PrivateKeySecretParameter":
            private_key_pem = read_parameter(
                parameter=output["OutputValue"], session=session, with_decryption=True
            )
    config_values["AWS_REGION"] = region

    # Read root CA
    with urllib.request.urlopen(
        "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
    ) as response:
        root_ca_pem = response.read().decode("utf-8")

    # process template files
    config_template = replace_variables(
        file="./templates/config.yaml", map=config_values
    )
    docker_compose_template = replace_variables(
        file="./templates/docker-compose.yml", map=config_values
    )

    # Write the files!
    with open(Path("./volumes/certs/device.pem.crt"), "w") as f:
        f.write(certificate_pem)
    with open(Path("./volumes/certs/private.pem.key"), "w") as f:
        f.write(private_key_pem)
    with open(Path("./volumes/certs/AmazonRootCA1.pem"), "w") as f:
        f.write(root_ca_pem)
    with open(Path("./volumes/config/config.yaml"), "w") as f:
        f.write(config_template)
    with open(Path("./docker-compose.yml"), "w") as f:
        f.write(docker_compose_template)

# with both valid, write:
#  cert, key, rootca to volumes/certs/
#  config to volumes/config/
#  docker-compose.yml to ./
