# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import boto3
from botocore.config import Config


def get_client(name):
    return boto3.client(
        name,
        region_name=os.environ["REGION"],
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )
