import sys
import json
import logging
import cfnresponse
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)

policyDocument = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Action": "iot:*", "Resource": "*"},
        {"Effect": "Allow", "Action": "greengrass:*", "Resource": "*"},
    ],
}
configDocument = {
    "coreThing": {
        "thingArn": "",
        "iotHost": "",
        "ggHost": "",
        "iotMqttPort": 443,
        "iotHttpPort": 443,
        "ggHttpPort": 443,
        "keepAlive": 600,
    },
    "runtime": {"cgroup": {"useSystemd": "yes"}},
    "managedRespawn": False,
    "crypto": {
        "principals": {
            "IoTCertificate": {
                "certificatePath": "file:///greengrass/certs/CERTIFICATE_NAME_HERE",
                "privateKeyPath": "file:///greengrass/certs/PRIVATE_KEY_FILENAME_HERE",
            }
        },
        "caPath": "file:///greengrass/certs/AmazonRootCA1.pem",
    },
}


def handler(event, context):
    responseData = {}
    try:
        logger.info("Received event: {}".format(json.dumps(event)))
        result = cfnresponse.FAILED
        client = boto3.client("iot")
        thingName = event["ResourceProperties"]["ThingName"]
        certArn = event["ResourceProperties"]["CertificateArn"]
        if event["RequestType"] == "Create":
            # Verify certificate is valid and correct region
            client.describe_certificate(certificateId=certArn.split("/")[-1])
            thing = client.create_thing(thingName=thingName)
            client.create_policy(
                policyName="{}-full-access".format(thingName),
                policyDocument=json.dumps(policyDocument),
            )
            response = client.attach_policy(
                policyName="{}-full-access".format(thingName), target=certArn
            )
            response = client.attach_thing_principal(
                thingName=thingName, principal=certArn
            )
            logger.info(
                "Created thing: %s and policy: %s"
                % (thingName, "{}-full-access".format(thingName))
            )
            result = cfnresponse.SUCCESS

            # Build config.json content and serialize
            configJSON = configDocument
            configJSON["coreThing"]["thingArn"] = thing["thingArn"]
            configJSON["coreThing"]["iotHost"] = client.describe_endpoint(
                endpointType="iot:Data-ATS"
            )["endpointAddress"]
            configJSON["coreThing"]["ggHost"] = (
                "greengrass-ats.iot."
                + configJSON["coreThing"]["iotHost"].split(".")[2]
                + ".amazonaws.com"
            )
            responseData["configJSON"] = json.dumps(configJSON)
        elif event["RequestType"] == "Update":
            logger.info("Updating thing: %s" % thingName)
            result = cfnresponse.SUCCESS
        elif event["RequestType"] == "Delete":
            logger.info("Deleting thing: %s and policy" % thingName)
            response = client.list_thing_principals(thingName=thingName)
            for i in response["principals"]:
                response = client.detach_thing_principal(
                    thingName=thingName, principal=i
                )
                response = client.detach_policy(
                    policyName="{}-full-access".format(thingName), target=i
                )
                response = client.delete_policy(
                    policyName="{}-full-access".format(thingName)
                )
                response = client.delete_thing(thingName=thingName)
            result = cfnresponse.SUCCESS
    except ClientError as e:
        logger.error("Error: {}".format(e))
        result = cfnresponse.FAILED
    logger.info(
        "Returning response of: {}, with result of: {}".format(result, responseData)
    )
    sys.stdout.flush()
    cfnresponse.send(event, context, result, responseData)
