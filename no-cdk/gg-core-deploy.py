#Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at

# http://aws.amazon.com/asl/

# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

# This is to create the following AWS resources using boto3
#   IoTThing
#   certificate/private key
#   iotPolicy
#   Role/RoleAlias to access IoT resources, S3, etc.
#   iotCredentialEndpoint for the current deployment account
#   S3 bucket
#   TokenExchangeRole

import shutil
import core_resource_handler
import json
import sys
import os
from pathlib import Path
import base64

FILE_PATH_WARNING = """
*************************************************************************
*** WARNING!!! WARNING!!! WARNING!!! WARNING!!! WARNING!!! WARNING!!! ***
***                                                                   ***
*** The current location of the repository has too long of a file     ***
*** path to successfully launch the docker container. The total       ***
*** length must be less than 104 characters. Reduce the file path by  ***
*** the value below, or the Greengrass service will not start.        ***
***                                                                   ***
*************************************************************************
"""

def verify_cwd():
    """
    Verify script is executed from docker/ directory,
    also, BIG ALERT if target file path to:
        docker/volumes/gg_root/v2/ipc.socket
    is greater than 104 characters.

    https://unix.stackexchange.com/questions/367008/why-is-socket-path-length-limited-to-a-hundred-chars
    """

    # check for sibling level directories and ../cdk
    docker_assets_path = Path("./docker/volumes")
    if not os.path.exists(docker_assets_path):
        print(f"Creating directory {docker_assets_path} shared with docker ")
        os.mkdir(docker_assets_path, 0o777)
        #sys.exit(1)
    # Determine current file path length and determine if full path to ipc.socket
    # From CWD addition characters to ipc.socket 37 characters
    cwd = Path(".", f"{docker_assets_path}/gg_root/ipc.socket")
    if len(str(cwd.absolute())) > 103:
        print(FILE_PATH_WARNING)
        print(
            f"********** Total current length is {len(str(cwd.absolute()))}, {len(str(cwd.absolute())) - 103} characters too long\n"
        )


def clean_config(dirs_to_clean: list):
    """remove all docker volume files, restore to unconfigured state"""
    print("Cleaning Docker volumes...")
    for dir in dirs_to_clean:
        path = Path(dir)
        if path.exists():
            print(f"Deleting files in {path}")
            shutil.rmtree(path)
        os.makedirs(path, 0o777)
        print(f"Directory '{dir} cleaned")

def makeid(length)->str:
    return base64.b64encode(os.urandom(32)).decode('ascii')[:length]


if __name__ == '__main__':

    numArg = len(sys.argv)
    if numArg != 2:
        print("please pass only one argument as the name of the 'thing' associated to greengrass instance")
        exit(1)

    docker_config_directories = [
        "./docker/volumes/certs",
        "./docker/volumes/config",
        "./docker/volumes/gg_root",
        "./docker/volumes/infout",
        "./docker/volumes/out",
        "./docker/volumes/data"
    ]

    verify_cwd()
    clean_config(docker_config_directories)
#    thing = sys.argv[1] + '-' + makeid(4)
    thing = sys.argv[1]
    result = core_resource_handler.create_resources(thing)
    print("Greengrass resource created:")
    print(json.dumps(result, indent=4))
    print("ThingArn: ", result["ThingArn"])
