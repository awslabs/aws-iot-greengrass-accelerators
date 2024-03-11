# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM amazonlinux:2

# Replace the args to lock to a specific version
ARG GREENGRASS_RELEASE_VERSION=2.10.3
ARG GREENGRASS_ZIP_FILE=greengrass-${GREENGRASS_RELEASE_VERSION}.zip
ARG GREENGRASS_RELEASE_URI=https://d2s8p88vqu9w66.cloudfront.net/releases/${GREENGRASS_ZIP_FILE}

# Author
LABEL maintainer="AWS IoT Greengrass"
# Greengrass Version
LABEL greengrass-version=${GREENGRASS_RELEASE_VERSION}

# Set up Greengrass v2 execution parameters
# TINI_KILL_PROCESS_GROUP allows forwarding SIGTERM to all PIDs in the PID group so Greengrass can exit gracefully
ENV TINI_KILL_PROCESS_GROUP=1 \
    GGC_ROOT_PATH=/greengrass/v2 \
    PROVISION=false \
    AWS_REGION=us-east-1 \
    THING_NAME=default_thing_name \
    THING_GROUP_NAME=default_thing_group_name \
    TES_ROLE_NAME=default_tes_role_name \
    TES_ROLE_ALIAS_NAME=default_tes_role_alias_name \
    COMPONENT_DEFAULT_USER=default_component_user \
    DEPLOY_DEV_TOOLS=false \
    INIT_CONFIG=default_init_config \
    TRUSTED_PLUGIN=default_trusted_plugin_path \
    THING_POLICY_NAME=default_thing_policy_name
RUN env

# Entrypoint script to install and run Greengrass
COPY "greengrass-entrypoint.sh" /

# Install Greengrass v2 dependencies
RUN yum update -y && yum install -y python37 tar unzip wget sudo procps which && \
    amazon-linux-extras enable python3.8 && yum install -y python3.8 java-11-amazon-corretto-headless && \
    wget $GREENGRASS_RELEASE_URI && \
    rm -rf /var/cache/yum && \
    chmod +x /greengrass-entrypoint.sh && \
    mkdir -p /opt/greengrassv2 $GGC_ROOT_PATH && unzip $GREENGRASS_ZIP_FILE -d /opt/greengrassv2 && rm $GREENGRASS_ZIP_FILE

# modify /etc/sudoers
COPY "modify-sudoers.sh" /
RUN chmod +x /modify-sudoers.sh
RUN ./modify-sudoers.sh

ENTRYPOINT ["/greengrass-entrypoint.sh"]