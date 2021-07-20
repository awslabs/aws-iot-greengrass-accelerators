# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import sys
import json
import logging as logger
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes

import time

logger.getLogger().setLevel(logger.INFO)

temp_event_create = {
    "RequestType": "Create",
    "ServiceToken": "arn:aws:lambda:us-west-2:904880203774:function:test1-IotThingCertPolicyFunctionframeworkonEvent86-CBSzZWfvqop6",
    "ResponseURL": "https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A904880203774%3Astack/test1/9a9c54b0-e8c5-11eb-a1c8-068346d307f3%7CGreengrassCoreIotThingCertPolicyFunctionA5730834%7Cd461a1a0-964e-4ade-ac1f-be88175a8d06?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20210719T191652Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIA54RCMT6SKBOPMYGJ%2F20210719%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Signature=3e1b109982a482443352ff382da9aa10686e13e94da2eeefc890af54875a8c89",
    "StackId": "arn:aws:cloudformation:us-west-2:904880203774:stack/test1/9a9c54b0-e8c5-11eb-a1c8-068346d307f3",
    "RequestId": "d461a1a0-964e-4ade-ac1f-be88175a8d06",
    "LogicalResourceId": "GreengrassCoreIotThingCertPolicyFunctionA5730834",
    "ResourceType": "AWS::CloudFormation::CustomResource",
    "ResourceProperties": {
        "ServiceToken": "arn:aws:lambda:us-west-2:904880203774:function:test1-IotThingCertPolicyFunctionframeworkonEvent86-CBSzZWfvqop6",
        "IoTPolicyName": "test1-greengrass-core-IAqStcTo",
        "ThingName": "test1-greengrass-core-PDGtAKoC",
        "IotPolicy": '"{\\n  Version: \\"2012-10-17\\",\\n  Statement: [\\n    {\\n      Effect: \\"Allow\\",\\n      Action: [\\"iot:Connect\\"],\\n      Resource: \\"arn:aws:iot:us-west-2:904880203774:client/greengrass-core*\\"\\n    },\\n    {\\n      Effect: \\"Allow\\",\\n      Action: [\\"iot:Receive\\", \\"iot:Publish\\"],\\n      Resource: [\\n        \\"arn:aws:iot:us-west-2:904880203774:topic/$aws/things/greengrass-core*/greengrass/health/json\\",\\n        \\"arn:aws:iot:us-west-2:904880203774:topic/$aws/things/greengrass-core*/greengrassv2/health/json\\",\\n        \\"arn:aws:iot:us-west-2:904880203774:topic/$aws/things/greengrass-core*/jobs/*\\",\\n        \\"arn:aws:iot:us-west-2:904880203774:topic/$aws/things/greengrass-core*/shadow/*\\"\\n      ]\\n    },\\n    {\\n      Effect: \\"Allow\\",\\n      Action: [\\"iot:Subscribe\\"],\\n      Resource: [\\n        \\"arn:aws:iot:us-west-2:904880203774:topicfilter/$aws/things/greengrass-core*/jobs/*\\",\\n        \\"arn:aws:iot:us-west-2:904880203774:topicfilter/$aws/things/greengrass-core*/shadow/*\\"\\n      ]\\n    },\\n    {\\n      Effect: \\"Allow\\",\\n      Action: [\\"iot:GetThingShadow\\", \\"iot:UpdateThingShadow\\", \\"iot:DeleteThingShadow\\"],\\n      Resource: [\\"arn:aws:iot:us-west-2:904880203774:thing/greengrass-core*\\"]\\n    },\\n    {\\n      Effect: \\"Allow\\",\\n      Action: \\"iot:AssumeRoleWithCertificate\\",\\n      Resource: \\"arn:aws:iot:us-west-2:904880203774:rolealias/test1-GreengrassV2TokenExchangeRole-3WORRPAi\\"\\n    },\\n    {\\n      Effect: \\"Allow\\",\\n      Action: [\\"greengrass:GetComponentVersionArtifact\\", \\"greengrass:ResolveComponentCandidates\\", \\"greengrass:GetDeploymentConfiguration\\"],\\n      Resource: \\"*\\"\\n    }\\n  ]\\n}"',
        "StackName": "test1",
    },
}

temp_environment = {
    "AWS_LAMBDA_FUNCTION_VERSION": "$LATEST",
    "LAMBDA_TASK_ROOT": "/var/task",
    "AWS_LAMBDA_LOG_GROUP_NAME": "/aws/lambda/test1-CreateIoTRoleAliasProviderA5DE3E61-rLnc8JosvWjj",
    "LD_LIBRARY_PATH": "/var/lang/lib:/lib64:/usr/lib64:/var/runtime:/var/runtime/lib:/var/task:/var/task/lib:/opt/lib",
    "AWS_LAMBDA_LOG_STREAM_NAME": "2021/07/16/[$LATEST]08359e000221485b8a001f401ee9f9b3",
    "AWS_LAMBDA_RUNTIME_API": "127.0.0.1:9001",
    "AWS_EXECUTION_ENV": "AWS_Lambda_python3.8",
    "AWS_LAMBDA_FUNCTION_NAME": "test1-CreateIoTRoleAliasProviderA5DE3E61-rLnc8JosvWjj",
    "AWS_XRAY_DAEMON_ADDRESS": "169.254.79.2:2000",
    "PATH": "/var/lang/bin:/usr/local/bin:/usr/bin/:/bin:/opt/bin",
    "AWS_DEFAULT_REGION": "us-west-2",
    "PWD": "/var/task",
    "LAMBDA_RUNTIME_DIR": "/var/runtime",
    "LANG": "en_US.UTF-8",
    "AWS_LAMBDA_INITIALIZATION_TYPE": "on-demand",
    "TZ": ":UTC",
    "AWS_REGION": "us-west-2",
    "SHLVL": "0",
    "_AWS_XRAY_DAEMON_ADDRESS": "169.254.79.2",
    "_AWS_XRAY_DAEMON_PORT": "2000",
    "AWS_XRAY_CONTEXT_MISSING": "LOG_ERROR",
    "_HANDLER": "role_alias.handler",
    "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "128",
    "PYTHONPATH": "/var/runtime",
    "_X_AMZN_TRACE_ID": "Root=1-60f1f774-66292ad5566a122178506fac;Parent=229af0ed792cd611;Sampled=0",
}


def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def create_resources(
    thing_name: str, iot_policy: str, iot_policy_name: str, stack_name: str
):
    """Create AWS IoT thing, certificate and attach certificate with policy and thing.
    Returns the Arns for the values and a Parameter Store Arn for the private key
    """
    c_iot = get_aws_client("iot")
    c_ssm = get_aws_client("ssm")

    response = {}

    # thing
    try:
        result = c_iot.create_thing(thingName=thing_name)
        response["ThingArn"] = result["thingArn"]
        response["ThingName"] = result["thingName"]
    except ClientError as e:
        logger.error(f"Error creating thing {thing_name}, {e}")
        sys.exit(1)

    # cert
    # Create certificate and private key
    key = ec.generate_private_key(curve=ec.SECP256R1(), backend=default_backend())
    private_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # Generate a CSR and set subject (CN=dispenserId)
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name(
                [
                    # Provide various details about who we are.
                    x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CO"),
                    x509.NameAttribute(NameOID.LOCALITY_NAME, "Denver"),
                    x509.NameAttribute(
                        NameOID.ORGANIZATION_NAME, "Greengrass Accelerator Testing"
                    ),
                    x509.NameAttribute(NameOID.COMMON_NAME, thing_name),
                ]
            )
        )
        .sign(key, hashes.SHA256(), default_backend())
    )
    try:
        result = c_iot.create_certificate_from_csr(
            certificateSigningRequest=str(
                csr.public_bytes(serialization.Encoding.PEM), "utf-8"
            ),
            setAsActive=True,
        )
        certificate_pem = result["certificatePem"]
        response["CertificateArn"] = result["certificateArn"]
    except ClientError as e:
        logger.error(f"Error creating certificate, {e}")
        sys.exit(1)

    # policy
    try:
        c_iot.create_policy(policyName=iot_policy_name, policyDocument=iot_policy)
    except ClientError as e:
        logger.error(f"Error creating policy {iot_policy_name}, {e}")
        sys.exit(1)

    # attach cert-pol
    try:
        c_iot.attach_policy(
            policyName=iot_policy_name, target=response["CertificateArn"]
        )
    except ClientError as e:
        logger.error(
            f"Error attaching certificate {response['CertificateArn']} to policy {iot_policy_name}, {e}"
        )
        sys.exit(1)

    # attach cert-thing
    try:
        c_iot.attach_thing_principal(
            thingName=thing_name,
            principal=response["CertificateArn"],
        )
    except ClientError as e:
        logger.error(
            f"Error attaching certificate {response['CertificateArn']} to thing {thing_name}, {e}"
        )
        sys.exit(1)

    # store certificate and private key in SSM param store
    try:
        parameter_private_key = f"/{stack_name}/{thing_name}/private_key"
        parameter_certificate_pem = f"/{stack_name}/{thing_name}/certificate_pem"
        # private key
        result = c_ssm.put_parameter(
            Name=parameter_private_key,
            Description=f"Certificate private key for IoT thing {thing_name}",
            Value=private_key,
            Type="SecureString",
            Tier="Standard",
        )
        response["PrivateKeySecretParameter"] = parameter_private_key
        # certificate pem
        result = c_ssm.put_parameter(
            Name=parameter_certificate_pem,
            Description=f"Certificate PEM for IoT thing {thing_name}",
            Value=certificate_pem,
            Type="String",
            Tier="Advanced",
        )
        response["CertificatePemParameter"] = parameter_certificate_pem
    except ClientError as e:
        logger.error(f"Error creating secure string parameters, {e}")
        sys.exit(1)

    # Additional data - these calls and responses are used in other constructs or external applications

    # Get the IoT-Data endpoint
    try:
        result = c_iot.describe_endpoint(endpointType="iot:Data-ATS")
        response["DataAtsEndpointAddress"] = result["endpointAddress"]
    except ClientError as e:
        logger.error(f"Could not obtain iot:Data-ATS endpoint, {e}")
        response["DataAtsEndpointAddress"] = "stack_error: see log files"
    return response


def delete_resources(
    thing_name: str, certificate_arn: str, iot_policy_name: str, stack_name: str
):
    """Delete thing, certificate, and policy in reverse order. Check for modifications
    since create (policy versions, etc)"""

    c_iot = get_aws_client("iot")
    c_ssm = get_aws_client("ssm")

    # delete ssm param store
    try:
        parameter_private_key = f"/{stack_name}/{thing_name}/private_key"
        parameter_certificate_pem = f"/{stack_name}/{thing_name}/certificate_pem"
        c_ssm.delete_parameters(
            Names=[parameter_private_key, parameter_certificate_pem]
        )
    except ClientError as e:
        logger.error(f"Unable to delete parameter store values, {e}")

    # delete policy (prune versions, detach from targets)
    # delete all non active policy versions
    try:
        response = c_iot.list_policy_versions(policyName=iot_policy_name)
        for version in response["policyVersions"]:
            if not version["isDefaultVersion"]:
                c_iot.delete_policy_version(
                    policyName=iot_policy_name, policyVersionId=version["versionId"]
                )
    except ClientError as e:
        logger.error(
            f"Unable to delete policy versions for policy {iot_policy_name}, {e}"
        )
    # Detach any principals
    try:
        response = c_iot.list_targets_for_policy(policyName=iot_policy_name)
        for target in response["targets"]:
            c_iot.detach_policy(policyName=iot_policy_name, target=target)
    except ClientError as e:
        logger.error(f"Unable to detach targets from policy {iot_policy_name}, {e}")
    # delete policy
    try:
        c_iot.delete_policy(policyName=iot_policy_name)
    except ClientError as e:
        logger.error(f"Unable to delete policy {iot_policy_name}, {e}")

    # delete cert
    # detach all policies and things from cert
    try:
        response = c_iot.list_principal_things(principal=certificate_arn)
        for thing in response["things"]:
            c_iot.detach_thing_principal(thingName=thing, principal=certificate_arn)
        response = c_iot.list_attached_policies(target=certificate_arn)
        for policy in response["policies"]:
            c_iot.detach_policy(policyName=policy, target=certificate_arn)
    except ClientError as e:
        logger.error(
            f"Unable to list or detach things or policies from certificate {certificate_arn}, {e}"
        )
    try:
        c_iot.update_certificate(
            certificateId=certificate_arn.split("/")[-1], newStatus="REVOKED"
        )
        c_iot.delete_certificate(certificateId=certificate_arn.split("/")[-1])
    except ClientError as e:
        logger.error(f"Unable to delete certificate {certificate_arn}, {e}")

    # delete thing
    # Check and detach principals attached to thing
    try:
        response = c_iot.list_thing_principals(thingName=thing_name)
        for principal in response["principals"]:
            c_iot.detach_thing_principal(thingName=thing_name, principal=principal)
    except ClientError as e:
        logger.error(f"Unable to list or detach principals from {thing_name}, {e}")
    try:
        print(f"test delete {thing_name}")
        c_iot.delete_thing(thingName=thing_name)
    except ClientError as e:
        logger.error(f"Unable to delete thing {thing_name}, {e}")


def handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))
    logger.info("Environment: %s", dict(os.environ))
    props = event["ResourceProperties"]
    physical_resource_id = ""
    try:
        # Check if this is a Create and we're failing Creates
        if event["RequestType"] == "Create" and event["ResourceProperties"].get(
            "FailCreate", False
        ):
            raise RuntimeError("Create failure requested, logging")
        elif event["RequestType"] == "Create":
            logger.info("Request CREATE")
            resp = create_resources(
                thing_name=props["ThingName"],
                iot_policy=props["IotPolicy"],
                iot_policy_name=props["IoTPolicyName"],
                stack_name=props["StackName"],
            )

            # set response data (PascalCase key)
            response_data = {
                "ThingArn": resp["ThingArn"],
                "CertificateArn": resp["CertificateArn"],
                "PrivateKeySecretParameter": resp["PrivateKeySecretParameter"],
                "CertificatePemParameter": resp["CertificatePemParameter"],
                "DataAtsEndpointAddress": resp["DataAtsEndpointAddress"],
            }
            physical_resource_id = response_data["CertificateArn"]
        elif event["RequestType"] == "Update":
            logger.info("Request UPDATE")
            response_data = {}
        elif event["RequestType"] == "Delete":
            logger.info("Request DELETE")
            resp = delete_resources(
                thing_name=props["ThingName"],
                certificate_arn=event["PhysicalResourceId"],
                iot_policy_name=props["IoTPolicyName"],
                stack_name=props["StackName"],
            )
            response_data = {}
            physical_resource_id = event["PhysicalResourceId"]
        else:
            logger.info("Should not get here in normal cases - could be REPLACE")

        output = {"PhysicalResourceId": physical_resource_id, "Data": response_data}
        logger.info("Output from Lambda: %s", json.dumps(output, indent=2))
        return output
    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    for env in temp_environment:
        os.environ[env] = temp_environment[env]

    # create
    print("running CREATE")
    response = handler(temp_event_create, {})
    # time.sleep(2)
    # temp_event["RequestType"] = "Delete"
    # response = handler(temp_event, {})
