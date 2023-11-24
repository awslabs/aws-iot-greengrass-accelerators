# Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at

# http://aws.amazon.com/asl/

# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.


# This is to destroy the aws resources contained in the manifest.json file
#   IoTThing
#   certificate/private key
#   iotPolicy
#   Role/RoleAlias to access IoT resources, S3, etc.
#   iotCredentialEndpoint for the current deployment account
#   S3 bucket
#   TokenExchangeRole

import core_resource_handler

if __name__ == '__main__':
    core_resource_handler.delete_resources_from_manifest('./resources/manifest.json')
    print('Greengrass resources deleted')

