#!/bin/bash

set -xe

# verify running from (working directory) script dir
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
if [[ $SCRIPT_DIR != $PWD ]]; then
    echo "test/build scrip must be from scripts directory, e.g., ~/.v2_test_build.sh"
    exit 1
fi

# check for AWS credential environment variables, region
# The credentials and region should match the profile normally used to deploy
if [[ -z "${AWS_ACCESS_KEY_ID}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY}" ]] || [[ -z "${AWS_DEFAULT_REGION}" ]]; then
    echo "Enviroment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION must be passed to this script."
    exit 1
else
    AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
    AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
    AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}"
fi

# Build and deploy `base` CDK stack
# Change to base CDK directory, install packages and build for base and common CDK constructs
cd $SCRIPT_DIR/../v2/base/cdk
npm install
npm run build
cdk deploy --require-approval "never" --ci

# Builder docker container and start Greengrass (compose-up)
cd $SCRIPT_DIR/../v2/base/docker



# wait until greengrass.log stablizes (fully deployed)

# Test `base` parts (helloworld output)

# Build and deploy os_cmd

# wait until os_cmd log file has valid output (or timeout after XXX minutes)

# cdk destory os_cmd

# Build and deploy etl_simple

# wait until etl-simple log file has valid output (or timeout after XXX minutes)

# cdk destroy etl_simple

# docker-compose stop
# clean docker volumes
# destroy base
cd $SCRIPT_DIR
cd ../v2/base/cdk
cdk destroy --force --ci

# Error exit

# if greengrass container running - docker-compose stop
# clean docker volumes
# if in os_cmd and cdk deployed, destroy os_cmd
# cdk destroy base