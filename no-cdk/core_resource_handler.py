# Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at

# http://aws.amazon.com/asl/

# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os
import sys
import json
import urllib

import yaml
import logging as logger
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes


logger.getLogger().setLevel(logger.INFO)

manifestFile = './resources/manifest.json'
credentialsDir = './docker/volumes/certs'
configYaml = './docker/volumes/config/config.yaml'
dockerComposeFile = './docker/docker-compose.yml'
gg_config = './gg-config/gg-config.yaml'


def getMinimalRolePolicy() -> str:
    rolePolicy = f'''{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Action": [
                "iot:DescribeCertificate",
                "iot:DescribeEndPoint", 
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "iot:Connect",
                "iot:Publish",
                "iot:Subscribe",
                "iot:Receive",
                "s3:*",
                "secretsmanager:GetSecretValue",
                "kinesis:*"
            ],
            "Resource": "*",
            "Effect": "Allow"
        }}
    ]
    }}'''
    return rolePolicy


def getIoTPolicy(thingname: str, rolealias: str) -> (str, str, str):
    c_sts = get_aws_client('sts')
    REGION = c_sts.meta.region_name
    ACCOUNT = c_sts.get_caller_identity().get('Account')
    THINGNAME = thingname
    ROLEALIAS = rolealias
    ggMinimalIoTPolicy = f'''\
{{
          "Version": "2012-10-17",
          "Statement": [ 
            {{ 
              "Effect": "Allow",
              "Action": ["iot:*"],
              "Resource": "*"
            }},
            {{
              "Effect": "Allow",
              "Action": "iot:AssumeRoleWithCertificate",
              "Resource": "arn:aws:iot:{REGION}:{ACCOUNT}:rolealias/{ROLEALIAS}"
            }},
            {{
            "Effect": "Allow",
            "Action": ["greengrass:*"],
            "Resource": "*"
            }}
          ]
        }}'''

    return ggMinimalIoTPolicy, ACCOUNT, REGION


def getIoTThingPolicyX(thingname: str, rolealias: str) -> (str, str, str):
    c_sts = get_aws_client('sts')
    REGION = c_sts.meta.region_name
    ACCOUNT = c_sts.get_caller_identity().get('Account')
    THINGNAME = thingname
    ROLEALIAS = rolealias
    ggMinimalIoTPolicy = f'''\
{{
          "Version": "2012-10-17",
          "Statement": [ 
            {{ 
              "Effect": "Allow",
              "Action": ["iot:*"],
              "Resource": "*"
            }},
            {{
              "Effect": "Allow",
              "Action": ["iot:Receive", "iot:Publish"],
              "Resource": [
                "arn:aws:iot:{REGION}:{ACCOUNT}:topic/$aws/things/{THINGNAME}*/greengrass/health/json",
                "arn:aws:iot:{REGION}:{ACCOUNT}:topic/$aws/things/{THINGNAME}*/greengrassv2/health/json",
                "arn:aws:iot:{REGION}:{ACCOUNT}:topic/$aws/things/{THINGNAME}*/jobs/*",
                "arn:aws:iot:{REGION}:{ACCOUNT}:topic/$aws/things/{THINGNAME}*/shadow/*"
              ]
            }},
            {{
              "Effect": "Allow",
              "Action": ["iot:Subscribe"],
              "Resource": [
                "arn:aws:iot:{REGION}:{ACCOUNT}:topicfilter/$aws/things/{THINGNAME}*/jobs/*",
                "arn:aws:iot:{REGION}:{ACCOUNT}:topicfilter/$aws/things/{THINGNAME}*/shadow/*"
              ]
            }},
            {{
              "Effect": "Allow",
              "Action": ["iot:GetThingShadow", "iot:UpdateThingShadow", "iot:DeleteThingShadow"],
              "Resource": ["arn:aws:iot:{REGION}:{ACCOUNT}:thing/{THINGNAME}*"]
            }},
            {{
              "Effect": "Allow",
              "Action": "iot:AssumeRoleWithCertificate",
              "Resource": "arn:aws:iot:{REGION}:{ACCOUNT}:rolealias/{ROLEALIAS}"
            }},
            {{
            "Effect": "Allow",
            "Action": [
                "greengrass:ListThingGroupsForCoreDevice",
                "greengrass:GetComponentVersionArtifact",
                "greengrass:ResolveComponentCandidates",
                "greengrass:GetDeploymentConfiguration"
            ],
            "Resource": "*"
            }}
          ]
        }}'''

    return ggMinimalIoTPolicy, ACCOUNT, REGION


def get_aws_client(name):
    return boto3.client(
        name,
        config=Config(retries={"max_attempts": 10, "mode": "standard"}),
    )


def create_rolealias(roleAliasName: str, roleName: str, policy_name: str, policy: str) -> dict:
    # this function create a role, a role alias and a policy for GG to use to connect to AWS services
    # it is executed by create_resources
    # Returns a dictionary with all resource created

    result = {}
    c_iam = get_aws_client("iam")
    assume_role_policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "credentials.iot.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    })
    try:
        response = c_iam.create_role(
            RoleName=roleName,
            AssumeRolePolicyDocument=assume_role_policy_document)
        logger.info(f"Created role {roleName}")
        roleArn = response["Role"]["Arn"]
        result['RoleArn'] = roleArn
        result['RoleName'] = roleName
        logger.info(f"Successfully created role {roleName}")
    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error creating role {roleName}, {e}")
        sys.exit(1)
    try:
        # create a policy to attach to the Role
        response = c_iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy
        )
        result['PolicyName'] = response['Policy']['PolicyName']
        result['PolicyArn'] = response['Policy']['Arn']
        logger.info(f"Successfully created policy {result['PolicyName']} for role {roleName}")
    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error creating policy for role {roleName}, {e}")
        sys.exit(1)

    try:
        response = c_iam.attach_role_policy(
            RoleName=roleName,
            PolicyArn=result['PolicyArn']
        )
        logger.info(f"Attached policy {result['PolicyName']} to role {roleName}")
    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error attaching policy {result['PolicyName']} to role {roleName}, {e}")
        sys.exit(1)
    # now we can create the roleAlias
    c_iot = get_aws_client("iot")
    try:
        response = c_iot.create_role_alias(
            roleAlias=roleAliasName,
            roleArn=roleArn,
        )
        result["RoleAliasArn"] = response["roleAliasArn"]
        result["RoleAliasName"] = roleAliasName
        logger.info(f"Successfully created Role Alias {roleAliasName}")
    except ClientError as e:
        write_manifest(result)
        logger.warning(
            f"Error calling iot.create_role_alias() for role alias {roleAliasName}, error: {e}"
        )
        sys.exit(1)
    return result


def create_resources(thing_name: str) -> dict:
    """
    Create AWS IoT thing, certificate and attach certificate with policy and thing.
    Returns a dictionary with all resource created
    """
    c_iot = get_aws_client("iot")
    iot_policy_name = thing_name + '-iot-policy'
    # first create an IoTRoleAlias (needed for the policy)
    alias_name = thing_name + '-ggRoleAliasName'
    role_name = thing_name + '-ggRoleName'
    role_policy_name = thing_name + '-ggRolePolicyName'
    result = create_rolealias(alias_name, role_name, role_policy_name, getMinimalRolePolicy())

    iot_policy, account, region = getIoTPolicy(thing_name, result['RoleAliasName'])
    result["ACCOUNT"] = account
    result["AWS_REGION"] = region
    # Create thing
    try:
        response = c_iot.create_thing(thingName=thing_name)
        result["ThingArn"] = response["thingArn"]
        result["ThingName"] = response["thingName"]
        logger.info(f"Successfully created iot Thing {thing_name}")

    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error creating thing {thing_name}, {e}")
        sys.exit(1)

    # create ThingGroup and assign it to the thing
    try:
        response = c_iot.create_thing_group(thingGroupName=thing_name + '-group')
        result["ThingGroupArn"] = response["thingGroupArn"]
        result["ThingGroupName"] = response["thingGroupName"]
        logger.info(f"Successfully created thing group {thing_name}-group")
        response = c_iot.add_thing_to_thing_group(
            thingGroupName=result["ThingGroupName"],
            thingGroupArn=result["ThingGroupArn"],
            thingName=thing_name,
            thingArn=result["ThingArn"])
        logger.info(f"Successfully added thing {thing_name} to thing group {result['ThingGroupName']}")

    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error creating thing group {thing_name}-group, {e}")
        sys.exit(1)

    encryption_algo = "RSA"
    # Create certificate and private key
    if encryption_algo == "ECC":
        key = ec.generate_private_key(curve=ec.SECP256R1(), backend=default_backend())
    elif encryption_algo == "RSA":
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )
    else:
        write_manifest(result)
        logger.error(
            f"Should not get here. Encryption algorithm of 'ECC' or 'RSA' expected, received {encryption_algo}. Exiting"
        )
        sys.exit(1)
    logger.info(f"Successfully created private key for iot Thing {thing_name}")
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
                    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                    x509.NameAttribute(NameOID.LOCALITY_NAME, "Los Gatos"),
                    x509.NameAttribute(
                        NameOID.ORGANIZATION_NAME, "PACE"
                    ),
                    x509.NameAttribute(NameOID.COMMON_NAME, thing_name),
                ]
            )
        )
        .sign(key, hashes.SHA256(), default_backend())
    )
    try:
        response = c_iot.create_certificate_from_csr(
            certificateSigningRequest=str(
                csr.public_bytes(serialization.Encoding.PEM), "utf-8"
            ),
            setAsActive=True,
        )
        certificate_pem = response["certificatePem"]
        result["CertificateArn"] = response["certificateArn"]
        logger.info(f"Successfully created Certificate {result['CertificateArn']} for iot Thing {thing_name}")
    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error creating certificate, {e}")
        sys.exit(1)

    # policy
    try:
        response = c_iot.create_policy(
            policyName=iot_policy_name, policyDocument=iot_policy
        )
        result["IotPolicyArn"] = response["policyArn"]
        result["IotPolicyName"] = iot_policy_name
        logger.info(f"Successfully created policy {iot_policy_name} for iot Thing {thing_name}")
    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error creating policy {iot_policy_name}, {e}")
        sys.exit(1)

    # attach certificate to policy
    try:
        c_iot.attach_policy(policyName=iot_policy_name, target=result["CertificateArn"])
        logger.info(f"Successfully attached policy {iot_policy_name} to Certificate for iot Thing {thing_name}")
    except ClientError as e:
        write_manifest(result)
        logger.error(
            f"Error attaching certificate {result['CertificateArn']} to policy {iot_policy_name}, {e}"
        )
        sys.exit(1)

    # attach certificate to thing
    try:
        c_iot.attach_thing_principal(thingName=thing_name, principal=result["CertificateArn"])
        logger.info(f"Successfully attached Certificate {result['CertificateArn']} to iot Thing {thing_name}")

    except ClientError as e:
        write_manifest(result)
        logger.error(
            f"Error attaching certificate {result['CertificateArn']} to thing {thing_name}, {e}"
        )
        sys.exit(1)

    # store certificate and private key in credentials directory
    try:
        # private key
        private_key_file = open(credentialsDir + "/private.pem.key", "w")
        private_key_file.write(private_key)
        private_key_file.close()
        # certificate pem
        certificate_file = open(credentialsDir + "/device.pem.crt", "w")
        certificate_file.write(certificate_pem)
        certificate_file.close()
        logger.info(f"Stored iot certificate/private key in {credentialsDir}")
    except ClientError as e:
        write_manifest(result)
        logger.error(f"Error writing credentials on {credentialsDir}, {e}")
        sys.exit(1)

    # Additional data - these calls and responses are used in other constructs or external applications

    # Get the IoT-Data endpoint
    try:
        response = c_iot.describe_endpoint(endpointType="iot:Data-ATS")
        result["DataAtsEndpointAddress"] = response["endpointAddress"]
        logger.info(f"Got iot:Data-ATS endpoint {result['DataAtsEndpointAddress']}")

    except ClientError as e:
        write_manifest(result)
        logger.error(f"Could not obtain iot:Data-ATS endpoint, {e}")
        sys.exit(1)

    # Get the Credential Provider endpoint
    try:
        response = c_iot.describe_endpoint(endpointType="iot:CredentialProvider")
        result["CredentialProviderEndpointAddress"] = response["endpointAddress"]
        logger.info(f"Got iot:CredentialProvider endpoint {result['CredentialProviderEndpointAddress']}")

    except ClientError as e:
        write_manifest(result)
        logger.error(f"Could not obtain iot:CredentialProvider endpoint, {e}")
        sys.exit(1)

    # write manifest
    write_manifest(result)
    logger.info(f"Successfully created manifest file {manifestFile}")

    # write config yaml file for greengrass docker
    write_configYaml(result)

    write_credentials(result)

    # write the docker-compose file with updated AWS REGION
    configureDockerComposeRegion('./docker-compose.template', dockerComposeFile, result['AWS_REGION'])

    # write component stack gg-config file to specify the deployment gg core device to deploy to
    write_thingArn_to_ggConfigYaml(result)

    # write environment variable file to launch the greengrass core device
    write_env_file(result)
    return result


def write_credentials(result: dict):
    # download amazon root certificate (if needed)
    if not os.path.isfile(credentialsDir + "/AmazonRootCA1.pem"):
        with urllib.request.urlopen(
                "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        ) as response:
            root_ca_pem = response.read().decode("utf-8")
        with open(credentialsDir + "/AmazonRootCA1.pem", "w") as f:
            f.write(root_ca_pem)

    # write private key on greengrass docker volume


def configureDockerComposeRegion(template: str, outputYaml: str, region: str):
    with open(template, 'r') as stream:
        try:
            # Converts yaml document to python object
            dockerCompose = yaml.safe_load(stream)
            dockerCompose['services']['greengrass']['environment']['AWS_DEFAULT_REGION'] = region
            # Printing dictionary
            print(json.dumps(dockerCompose, indent=4))
            # writing to yaml file
            with open(outputYaml, 'w') as outfile:
                yaml.dump(dockerCompose, outfile, sort_keys=False, explicit_start=False, explicit_end=False)
                outfile.close()

        except yaml.YAMLError as e:
            print(e)


def write_manifest(result: dict):
    try:
        # store result in ./resources/manifest.json file
        manifest = open(manifestFile, "w")
        manifest.write(json.dumps(result, indent=4, sort_keys=True))
        manifest.close()
    except ClientError as e:
        logger.error(f"Error writing {manifestFile}.json, {e}")
        sys.exit(1)
    return result


''' this is the expected configuration file for greengrass docker
system:
  certificateFilePath: "/tmp/certs/device.pem.crt"
  privateKeyPath: "/tmp/certs/private.pem.key"
  rootCaPath: "/tmp/certs/AmazonRootCA1.pem"
  rootpath: "/greengrass/v2"
  thingName: "${THING_NAME}"
services:
  aws.greengrass.Nucleus:
    componentType: "NUCLEUS"
    version: "2.11.2"
    configuration:
      awsRegion: "${AWS_REGION}"
      iotRoleAlias: "${IOT_ROLE_ALIAS}"
      iotDataEndpoint: "${DATA_ATS_ENDPOINT}"
      iotCredEndpoint: "${CREDENTIAL_PROVIDER_ENDPOINT}"
      mqtt:
        port: 8883
'''


def write_configYaml(result: dict):
    yamlDict = dict()
    yamlDict['system'] = dict()
    yamlDict['services'] = dict()
    yamlDict['services']['aws.greengrass.Nucleus'] = dict()
    yamlDict['services']['aws.greengrass.Nucleus']['configuration'] = dict()
    yamlDict['services']['aws.greengrass.Nucleus']['configuration']['mqtt'] = dict()
    yamlDict['system']['certificateFilePath'] = "/tmp/certs/device.pem.crt"
    yamlDict['system']['privateKeyPath'] = "/tmp/certs/private.pem.key"
    yamlDict['system']['rootCaPath'] = "/tmp/certs/AmazonRootCA1.pem"
    yamlDict['system']['rootpath'] = "/greengrass/v2"
    yamlDict['system']['thingName'] = result['ThingName']
    yamlDict['services']['aws.greengrass.Nucleus']['componentType'] = "NUCLEUS"
    yamlDict['services']['aws.greengrass.Nucleus']['version'] = "2.11.2"
    yamlDict['services']['aws.greengrass.Nucleus']['configuration']['awsRegion'] = result['AWS_REGION']
    yamlDict['services']['aws.greengrass.Nucleus']['configuration']['iotRoleAlias'] = result['RoleAliasName']
    yamlDict['services']['aws.greengrass.Nucleus']['configuration']['iotDataEndpoint'] = result[
        'DataAtsEndpointAddress']
    yamlDict['services']['aws.greengrass.Nucleus']['configuration']['iotCredEndpoint'] = result[
        'CredentialProviderEndpointAddress']
    yamlDict['services']['aws.greengrass.Nucleus']['configuration']['mqtt']['port'] = 8883

    try:
        # store deployment results in ggConfigYaml file
        with open(configYaml, 'w') as outfile:
            yaml.dump(yamlDict, outfile, sort_keys=False, explicit_start=True, explicit_end=False)
            outfile.close()
    except ClientError as e:
        logger.error(f"Error writing {configYaml}.yaml, {e}")
        sys.exit(1)
    return result


def write_thingArn_to_ggConfigYaml(result: dict):
    # if gg-config.yaml exists, keep the components list 
    yamlDict = dict()
    if os.path.isfile(gg_config):
        yamlDict = dict()
        with open(gg_config, 'r') as stream:
            try:
                # Converts yaml document to python object
                yamlDict = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)
    else:
        yamlDict['components'] = []
    
    yamlDict['thingArn'] = result['ThingArn']
    yamlDict['thingGroupArn'] = result['ThingGroupArn']
    yamlDict['thingName'] = result['ThingName']

    try:
        # store deployment results in ggConfigYaml file
        with open(gg_config, 'w') as outfile:
            yaml.dump(yamlDict, outfile, sort_keys=False, explicit_start=True, explicit_end=False)
            outfile.close()
    except ClientError as e:
        logger.error(f"Error writing {gg_config}.yaml, {e}")
        sys.exit(1)
    return result


def delete_resources_from_manifest(manifestFile: str):
    manifest = open(manifestFile, "r")
    manifest_json = json.loads(manifest.read())
    manifest.close()
    # delete IAM resources: Role, RoleAlias, Policy

    role = manifest_json.get("RoleName")
    role_alias = manifest_json.get("RoleAliasName")
    policy_name = manifest_json.get("PolicyName")
    delete_iam_resources(
        role=role,
        policyArn=manifest_json.get("PolicyArn"),
        policyName=policy_name
    )

    # delete IoT resources
    thing_name = manifest_json.get("ThingName")
    certificate_arn = manifest_json.get("CertificateArn")
    iot_policy_name = manifest_json.get("IotPolicyName")
    delete_iot_resources(
        thing_name=thing_name,
        certificate_arn=certificate_arn,
        iot_policy_name=iot_policy_name,
        roleAlias=role_alias,
        thingGroupName=manifest_json.get("ThingGroupName")
    )
    return


def delete_iam_resources(role, policyArn, policyName):
    c_iam = get_aws_client("iam")
    # delete IAM resources: Role, RoleAlias, Policy
    try:
        if role and policyArn:
            c_iam.detach_role_policy(RoleName=role, PolicyArn=policyArn)
            logger.info(f"Detached policy {policyName} from role {role}")
        if policyArn:
            c_iam.delete_policy(PolicyArn=policyArn)
            logger.info(f"Deleted policy {policyName}")
        if role:
            c_iam.delete_role(RoleName=role)
            logger.info(f"Deleted role {role}")

    except ClientError as e:
        logger.error(f"Unable to delete IAM resources, {e}")
        sys.exit(1)


def delete_iot_resources(thing_name, certificate_arn, iot_policy_name, roleAlias, thingGroupName):
    """Delete thing, certificate, and policy in reverse order. Check for modifications
    since create (policy versions, etc)"""

    c_iot = get_aws_client("iot")

    # delete policy (prune versions, detach from targets)
    # delete all non active policy versions
    try:
        response = c_iot.list_policy_versions(policyName=iot_policy_name)
        for version in response["policyVersions"]:
            if not version["isDefaultVersion"]:
                c_iot.delete_policy_version(policyName=iot_policy_name, policyVersionId=version["versionId"])
        logger.info(f"Deleted all policy versions for policy {iot_policy_name}")
    except ClientError as e:
        logger.error(
            f"Unable to delete policy versions for policy {iot_policy_name}, {e}"
        )
    # Detach any principals
    try:
        response = c_iot.list_targets_for_policy(policyName=iot_policy_name)
        for target in response["targets"]:
            c_iot.detach_policy(policyName=iot_policy_name, target=target)
        logger.info(f"Detached targets from policy {iot_policy_name}")
    except ClientError as e:
        logger.error(f"Unable to detach targets from policy {iot_policy_name}, {e}")
    # delete policy and roleAlias
    try:
        c_iot.delete_policy(policyName=iot_policy_name)
        logger.info(f"Deleted policy {iot_policy_name}")
        c_iot.delete_role_alias(roleAlias=roleAlias)
        logger.info(f"Deleted roleAlias {roleAlias}")
    except ClientError as e:
        logger.error(f"Unable to delete policy {iot_policy_name}, {e}")

    # delete cert
    # detach all policies and things from cert
    try:
        response = c_iot.list_principal_things(principal=certificate_arn)
        for thing in response["things"]:
            c_iot.detach_thing_principal(thingName=thing, principal=certificate_arn)
        logger.info(f"Detached things from certificate {certificate_arn}")
        response = c_iot.list_attached_policies(target=certificate_arn)
        for policy in response["policies"]:
            c_iot.detach_policy(policyName=policy["policyName"], target=certificate_arn)
        logger.info(f"Detached policies from certificate {certificate_arn}")
    except ClientError as e:
        logger.error(
            f"Unable to list or detach things or policies from certificate {certificate_arn}, {e}"
        )
    try:
        c_iot.update_certificate(certificateId=certificate_arn.split("/")[-1], newStatus="REVOKED")
        logger.info(f"Revoked certificate {certificate_arn}")
        c_iot.delete_certificate(certificateId=certificate_arn.split("/")[-1])
        logger.info(f"Deleted certificate {certificate_arn}")
    except ClientError as e:
        logger.error(f"Unable to delete certificate {certificate_arn}, {e}")

    # delete thing
    # Check and detach principals attached to thing
    try:
        response = c_iot.list_thing_principals(thingName=thing_name)
        for principal in response["principals"]:
            c_iot.detach_thing_principal(thingName=thing_name, principal=principal)
        logger.info(f"Detached principals from {thing_name}")
    except ClientError as e:
        logger.error(f"Unable to list or detach principals from {thing_name}, {e}")
    try:
        c_iot.delete_thing(thingName=thing_name)
        logger.info(f"Deleted thing {thing_name}")
    except ClientError as e:
        logger.error(f"Error calling iot.delete_thing() for thing: {thing_name}, {e}")

    # delete the credential files on local file system
    try:
        privateKeyFile = credentialsDir + '/private.pem.key'
        if os.path.isfile(privateKeyFile):
            os.remove(privateKeyFile)
        certificateFile = credentialsDir + '/device.pem.crt'
        if os.path.isfile(certificateFile):
            os.remove(certificateFile)
        logger.info(f"Deleted credential files on local file system")
    except ClientError as e:
        logger.error(f"Unable to delete credential files on local file system, {e}")

    # delete thing group
    try:
        c_iot.delete_thing_group(thingGroupName=thingGroupName)
        logger.info(f"Deleted thing group {thingGroupName}")
    except ClientError as e:
        logger.error(f"Unable to delete thing group {thingGroupName}, {e}")


def write_env_file(result: dict):
    c_sts = get_aws_client('sts')
    REGION = c_sts.meta.region_name

    try:
        # store result in .env file
        env_file = open("./.env", "w")
        env_file.write(f'GGC_ROOT_PATH="/greengrass/v2"\n')
        env_file.write(f'PROVISION=false\n')
        env_file.write(f'AWS_DEFAULT_REGION="{REGION}"\n')
#        env_file.write(f'COMPONENT_DEFAULT_USER="ggc_user:ggc_group"\n')
        env_file.write(f'COMPONENT_DEFAULT_USER="default_component_user"\n')
        env_file.write(f'DEPLOY_DEV_TOOLS=false\n')
        env_file.write(f'THING_NAME="{result["ThingName"]}"\n')
        env_file.write(f'THING_GROUP_NAME="{result["ThingGroupName"]}"\n')
        env_file.write(f'THING_POLICY_NAME="{result["IotPolicyName"]}"\n')
        env_file.write(f'TRUSTED_PLUGIN="default_trusted_plugin_path"\n')
        env_file.write(f'TES_ROLE_NAME="{result["RoleName"]}"\n')
        env_file.write(f'TES_ROLE_ALIAS_NAME="{result["RoleAliasName"]}"\n')
        env_file.write(f'INIT_CONFIG="./docker/volumes/config/config.yaml"\n');
        env_file.close()
    except ClientError as e:
        logger.error(f"Error writing ./.env file, {e}")
        sys.exit(1)
    return result
