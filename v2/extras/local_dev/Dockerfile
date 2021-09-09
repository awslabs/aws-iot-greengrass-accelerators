# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM amazonlinux:2

# This builds a development image for Visual Studio Code and other local access
# to develop and deploy components

# Replace the args to lock to a specific version
ARG GREENGRASS_RELEASE_VERSION=2.4.0
ARG GREENGRASS_ZIP_FILE=greengrass-${GREENGRASS_RELEASE_VERSION}.zip
ARG GREENGRASS_RELEASE_URI=https://d2s8p88vqu9w66.cloudfront.net/releases/${GREENGRASS_ZIP_FILE}
ARG GREENGRASS_ZIP_SHA256=greengrass.zip.sha256

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
ENV PATH="$PATH:${GGC_ROOT_PATH}/bin"
RUN env

# Development Entrypoint script to install and run Greengrass
COPY "dockerfile-assets/greengrass-entrypoint-dev.sh" /greengrass-entrypoint.sh
COPY "dockerfile-assets/${GREENGRASS_ZIP_SHA256}" /

# Install Greengrass v2 dependencies
RUN yum update -y && yum install -y python37 tar unzip wget sudo procps which && \
    amazon-linux-extras enable python3.8 && yum install -y python3.8 java-11-amazon-corretto-headless && \
    wget $GREENGRASS_RELEASE_URI && sha256sum -c ${GREENGRASS_ZIP_SHA256} && \
    rm -rf /var/cache/yum && \
    chmod +x /greengrass-entrypoint.sh && \
    mkdir -p /opt/greengrassv2 $GGC_ROOT_PATH && unzip $GREENGRASS_ZIP_FILE -d /opt/greengrassv2 && rm $GREENGRASS_ZIP_FILE && rm $GREENGRASS_ZIP_SHA256

# modify /etc/sudoers
COPY "dockerfile-assets/modify-sudoers.sh" /
RUN chmod +x /modify-sudoers.sh
RUN ./modify-sudoers.sh

############## BEGIN DEVELOPEMENT ADDITIONS
# Install development packages
RUN yum update -y && yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    yum -y install net-tools iputils less yum-utils zip && \
    amazon-linux-extras enable docker && yum install -y docker && \
    rm -rf /var/cache/yum && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && unzip -d /tmp -q /tmp/awscliv2.zip && \
    /tmp/aws/install && rm -rf /tmp/aws && rm /tmp/awscliv2.zip

# Pre-create ggc_user, ggc_group, and add to docker group
RUN useradd ggc_user && groupadd ggc_group && usermod -a -G ggc_group,docker ggc_user

# Install common development tools at file system level (outside Greengrass)
RUN pip3 install black

# Create directory where folder volume will be mapped
RUN mkdir -p /opt/component_development

############## END DEVELOPEMENT ADDITIONS

ENTRYPOINT ["/greengrass-entrypoint.sh"]