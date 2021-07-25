#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Allow the root user to execute commands as other users

set -e

# Grab the line number for the root user entry
ROOT_LINE_NUM=$(grep -n "^root" /etc/sudoers | cut -d : -f 1)

# Check if the root user is already configured to execute commands as other users
if sudo sed -n "${ROOT_LINE_NUM}p" /etc/sudoers | grep -q "ALL=(ALL:ALL)" ; then
  echo "Root user is already configured to execute commands as other users."
  return 0
fi

echo "Attempting to safely modify /etc/sudoers..."

# Take a backup of /etc/sudoers
sudo cp /etc/sudoers /tmp/sudoers.bak

# Replace `ALL=(ALL)` with `ALL=(ALL:ALL)` to allow the root user to execute commands as other users
sudo sed -i "$ROOT_LINE_NUM s/ALL=(ALL)/ALL=(ALL:ALL)/" /tmp/sudoers.bak

# Validate syntax of backup file
sudo visudo -cf /tmp/sudoers.bak
if [ $? -eq 0 ]; then
  # Replace the sudoers file with the new only if syntax is correct.
  sudo mv /tmp/sudoers.bak /etc/sudoers
  echo "Successfully modified /etc/sudoers. Root user is now configured to execute commands as other users."
else
  echo "Error while trying to modify /etc/sudoers, please edit manually."
  exit 1
fi