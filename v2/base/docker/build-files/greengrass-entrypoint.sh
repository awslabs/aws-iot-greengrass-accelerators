#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

set -e

#Disable job control so that all child processes run in the same process group as the parent
set +m

# Path that initial installation files are copied to
INIT_JAR_PATH=/opt/greengrassv2
#Default options
OPTIONS="-Droot=${GGC_ROOT_PATH} -Dlog.store=FILE -Dlog.level=${LOG_LEVEL} -jar ${INIT_JAR_PATH}/lib/Greengrass.jar --provision ${PROVISION} --deploy-dev-tools ${DEPLOY_DEV_TOOLS} --aws-region ${AWS_REGION} --start false"

parse_options() {

	# If provision is true
	if [ ${PROVISION} = "true" ]; then

		if [ ! -f "/root/.aws/credentials" ] && ([[ -z "${AWS_ACCESS_KEY_ID}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY}" ]] || [[ -z "${AWS_SESSION_TOKEN}" ]]); then
			echo "Provision is set to true, but credentials not found, neither file exist at /root/.aws/credentials nor set in environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN) . Please attach credentials and retry."
			exit 1
		fi

		# If thing name is specified, add optional argument
		# If not specified, reverts to default of "GreengrassV2IotThing_" plus a random UUID.
		if [ ${THING_NAME} != default_thing_name ]; then
		    OPTIONS="${OPTIONS} --thing-name ${THING_NAME}"


		fi
		# If thing group name is specified, add optional argument
		if [ ${THING_GROUP_NAME} != default_thing_group_name ]; then
			OPTIONS="${OPTIONS} --thing-group-name ${THING_GROUP_NAME}"

		fi

               # If thing group policy is specified, add optional argument
               if [ ${THING_POLICY_NAME} != default_thing_policy_name ]; then
                       OPTIONS="${OPTIONS} --thing-policy-name ${THING_POLICY_NAME}"
               fi
	fi

  # If TRUSTED_PLUGIN is specified, add optional argument
  # If not specified, it will not use this argument
	if [ ${TRUSTED_PLUGIN} != default_trusted_plugin_path ]; then
	  OPTIONS="${OPTIONS} --trusted-plugin ${TRUSTED_PLUGIN}"
	fi

	# If TES role name is specified, add optional argument
	# If not specified, reverts to default of "GreengrassV2TokenExchangeRole"
	if [ ${TES_ROLE_NAME} != default_tes_role_name ]; then
		OPTIONS="${OPTIONS} --tes-role-name ${TES_ROLE_NAME}"
	fi

	# If TES role name is specified, add optional argument
	# If not specified, reverts to default of "GreengrassV2TokenExchangeRoleAlias"
	if [ ${TES_ROLE_ALIAS_NAME} != default_tes_role_alias_name ]; then
		OPTIONS="${OPTIONS} --tes-role-alias-name ${TES_ROLE_ALIAS_NAME}"
	fi

	# If component default user is specified, add optional argument
	# If not specified, reverts to ggc_user:ggc_group
	if [ ${COMPONENT_DEFAULT_USER} != default_component_user ]; then
		OPTIONS="${OPTIONS} --component-default-user ${COMPONENT_DEFAULT_USER}"
	fi

	# Use optional init config argument
	# If this option is specified, the config file must be mounted to this location
	if [ ${INIT_CONFIG} != default_init_config ]; then
		if [ -f ${INIT_CONFIG} ]; then
			echo "Using specified init config file at ${INIT_CONFIG}"
			OPTIONS="${OPTIONS} --init-config ${INIT_CONFIG}"
	    else
	    	echo "WARNING: Specified init config file does not exist at ${INIT_CONFIG} !"
	    fi
	fi

	echo "Running Greengrass with the following options: ${OPTIONS}"
}

# If we have not already installed Greengrass
if [ ! -d $GGC_ROOT_PATH/alts/current/distro ]; then
	# Install Greengrass via the main installer, but do not start running
	echo "Installing Greengrass for the first time..."
	parse_options
	java ${OPTIONS}
else
	echo "Reusing existing Greengrass installation..."
fi

#Make loader script executable
echo "Making loader script executable..."
chmod +x $GGC_ROOT_PATH/alts/current/distro/bin/loader

echo "Starting Greengrass..."

# Start greengrass kernel via the loader script and register container as a thing
exec $GGC_ROOT_PATH/alts/current/distro/bin/loader