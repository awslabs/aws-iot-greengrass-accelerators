#
# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

from greengrass_common.env_vars import GGC_MAX_INTERFACE_VERSION
from greengrass_common.parse_version import parse_version

sdk_IV_major = 1
sdk_IV_minor = 2


class ValidationUtil(object):
    @staticmethod
    def validate_required_gg_interface():
        max_IV_major, max_IV_minor = parse_version(GGC_MAX_INTERFACE_VERSION)
        if int(sdk_IV_major) != int(max_IV_major) or int(sdk_IV_minor) > int(max_IV_minor):
            err = ValueError('There was a version incompatibility between the Greengrass Machine Learning SDK used ' +
                             'by your function and the Greengrass Core. Please visit the AWS Greengrass Developer Guide for version compatibility information')
            raise err
