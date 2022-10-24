#!/bin/bash


# Functions used by script
wait_str() {
  local file="$1"; shift
  local search_term="$1"; shift
  local wait_time="${1:-5m}"; shift # 5 minutes as default timeout

  (timeout $wait_time tail -F -n +1 "$file" &) | grep -q "$search_term" && return 0

  echo "Timeout of $wait_time reached. Unable to find '$search_term' in '$file'"
  return 1
}

wait_logfile() {
  echo "Waiting for logfile..."
  local server_log="$1"; shift
  local wait_time="$1"; shift

  wait_file "$server_log" "$wait_time" || { echo "Logfile file missing: '$server_log'"; return 1; }
}

wait_file() {
  local file="$1"; shift
  local wait_seconds="${1:-10}"; shift # 10 seconds as default timeout

  until test $((wait_seconds--)) -eq 0 -o -f "$file" ; do sleep 1; done

  ((++wait_seconds))
}

# timeout script if running on macOS
# Originally found on SO: http://stackoverflow.com/questions/601543/command-line-command-to-auto-kill-a-command-after-a-certain-amount-of-time
if [[ "$OSTYPE" == "darwin"* ]]; then
    function timeout() { perl -e 'alarm shift; exec @ARGV' "$@"; }
fi

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
python3 config_docker.py --clean
python3 config_docker.py --use-envars
docker-compose up -d

# wait until greengrass.log stablizes (fully deployed)
# wait_logfile $SCRIPT_DIR/../v2/base/docker/volues/gg_root/logs/greengrass.log 5m && \
# echo -e "Received empty jobs in notification . {ThingName=gg-accel-base-greengrass-core"
exit 0



# Test `base` parts (helloworld output)

# Build and deploy os_cmd

# wait until os_cmd log file has valid output (or timeout after XXX minutes)

# cdk destory os_cmd

# Build and deploy etl_simple

# wait until etl-simple log file has valid output (or timeout after XXX minutes)

# cdk destroy etl_simple

# docker-compose stop base
cd $SCRIPT_DIR/../v2/base/docker
docker-compose stop
python3 config_docker.py --clean


# destroy base
cd $SCRIPT_DIR
cd ../v2/base/cdk
cdk destroy --force --ci
