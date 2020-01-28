"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const cdk = require("@aws-cdk/core");
const cr_iot_thing_cert_policy_1 = require("./cr-create-iot-thing-cert-policy/cr-iot-thing-cert-policy");
const cr_greengrass_service_role_1 = require("./cr-greengrass-service-role/cr-greengrass-service-role");
/**
 * A stack that sets up MyCustomResource and shows how to get an attribute from it
 */
class GreengrassStreamManagerStack extends cdk.Stack {
    constructor(scope, id, props) {
        super(scope, id, props);
        // Create AWS IoT Thing/Certificate/Policy as basis for Greengrass Core
        const crIoTResource = new cr_iot_thing_cert_policy_1.CustomResourceIoTThingCertPolicy(this, 'CreateThingCertPolicyCustomResource', {
            functionName: id + '-CreateThingCertPolicyFunction',
            stackName: id,
        });
        new cdk.CfnOutput(this, 'CertificatePEM', {
            description: 'Certificate of Greengrass Core thing',
            value: crIoTResource.certificatePem
        });
        new cdk.CfnOutput(this, 'PrivateKeyPEM', {
            description: 'Private Key of Greengrass Core thing',
            value: crIoTResource.privateKeyPem
        });
        // Create Greengrass Service role with permissions the Core's resources should have
        new cr_greengrass_service_role_1.CustomResourceGreengrassServiceRole(this, "GreengrassRoleCustomResource", {
            functionName: id + '-GreengrassRoleFunction',
            stackName: id,
            rolePolicy: {
                "Version": "2012-10-17",
                "Statement": {
                    "Effect": "Allow",
                    "Action": "iot:*",
                    "Resource": "*",
                }
            },
        });
    }
}
// Pre-stack creation steps
// Create stack
const app = new cdk.App();
new GreengrassStreamManagerStack(app, 'gg-stream-accel');
app.synth();
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyJpbmRleC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBLHFDQUFzQztBQUN0Qyx5R0FBOEc7QUFDOUcsd0dBQThHO0FBRTlHOztHQUVHO0FBQ0gsTUFBTSw0QkFBNkIsU0FBUSxHQUFHLENBQUMsS0FBSztJQUNsRCxZQUFZLEtBQWMsRUFBRSxFQUFVLEVBQUUsS0FBc0I7UUFDNUQsS0FBSyxDQUFDLEtBQUssRUFBRSxFQUFFLEVBQUUsS0FBSyxDQUFDLENBQUM7UUFHeEIsdUVBQXVFO1FBQ3ZFLE1BQU0sYUFBYSxHQUFHLElBQUksMkRBQWdDLENBQUMsSUFBSSxFQUFFLHFDQUFxQyxFQUFFO1lBQ3RHLFlBQVksRUFBRSxFQUFFLEdBQUcsZ0NBQWdDO1lBQ25ELFNBQVMsRUFBRSxFQUFFO1NBQ2QsQ0FBQyxDQUFDO1FBQ0gsSUFBSSxHQUFHLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRSxnQkFBZ0IsRUFBRTtZQUN4QyxXQUFXLEVBQUUsc0NBQXNDO1lBQ25ELEtBQUssRUFBRSxhQUFhLENBQUMsY0FBYztTQUNwQyxDQUFDLENBQUM7UUFDSCxJQUFJLEdBQUcsQ0FBQyxTQUFTLENBQUMsSUFBSSxFQUFFLGVBQWUsRUFBRTtZQUN2QyxXQUFXLEVBQUUsc0NBQXNDO1lBQ25ELEtBQUssRUFBRSxhQUFhLENBQUMsYUFBYTtTQUNuQyxDQUFDLENBQUM7UUFFSCxtRkFBbUY7UUFDbkYsSUFBSSxnRUFBbUMsQ0FBQyxJQUFJLEVBQUUsOEJBQThCLEVBQUU7WUFDNUUsWUFBWSxFQUFFLEVBQUUsR0FBRyx5QkFBeUI7WUFDNUMsU0FBUyxFQUFFLEVBQUU7WUFDYixVQUFVLEVBQUU7Z0JBQ1YsU0FBUyxFQUFFLFlBQVk7Z0JBQ3ZCLFdBQVcsRUFBRTtvQkFDVCxRQUFRLEVBQUUsT0FBTztvQkFDakIsUUFBUSxFQUFFLE9BQU87b0JBQ2pCLFVBQVUsRUFBRSxHQUFHO2lCQUNsQjthQUNKO1NBQ0EsQ0FBQyxDQUFDO0lBSUwsQ0FBQztDQUNGO0FBRUQsMkJBQTJCO0FBRTNCLGVBQWU7QUFDZixNQUFNLEdBQUcsR0FBRyxJQUFJLEdBQUcsQ0FBQyxHQUFHLEVBQUUsQ0FBQztBQUMxQixJQUFJLDRCQUE0QixDQUFDLEdBQUcsRUFBRSxpQkFBaUIsQ0FBQyxDQUFDO0FBQ3pELEdBQUcsQ0FBQyxLQUFLLEVBQUUsQ0FBQyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCBjZGsgPSByZXF1aXJlKCdAYXdzLWNkay9jb3JlJyk7XG5pbXBvcnQgeyBDdXN0b21SZXNvdXJjZUlvVFRoaW5nQ2VydFBvbGljeSB9IGZyb20gJy4vY3ItY3JlYXRlLWlvdC10aGluZy1jZXJ0LXBvbGljeS9jci1pb3QtdGhpbmctY2VydC1wb2xpY3knO1xuaW1wb3J0IHsgQ3VzdG9tUmVzb3VyY2VHcmVlbmdyYXNzU2VydmljZVJvbGUgfSBmcm9tICcuL2NyLWdyZWVuZ3Jhc3Mtc2VydmljZS1yb2xlL2NyLWdyZWVuZ3Jhc3Mtc2VydmljZS1yb2xlJztcblxuLyoqXG4gKiBBIHN0YWNrIHRoYXQgc2V0cyB1cCBNeUN1c3RvbVJlc291cmNlIGFuZCBzaG93cyBob3cgdG8gZ2V0IGFuIGF0dHJpYnV0ZSBmcm9tIGl0XG4gKi9cbmNsYXNzIEdyZWVuZ3Jhc3NTdHJlYW1NYW5hZ2VyU3RhY2sgZXh0ZW5kcyBjZGsuU3RhY2sge1xuICBjb25zdHJ1Y3RvcihzY29wZTogY2RrLkFwcCwgaWQ6IHN0cmluZywgcHJvcHM/OiBjZGsuU3RhY2tQcm9wcykge1xuICAgIHN1cGVyKHNjb3BlLCBpZCwgcHJvcHMpO1xuXG5cbiAgICAvLyBDcmVhdGUgQVdTIElvVCBUaGluZy9DZXJ0aWZpY2F0ZS9Qb2xpY3kgYXMgYmFzaXMgZm9yIEdyZWVuZ3Jhc3MgQ29yZVxuICAgIGNvbnN0IGNySW9UUmVzb3VyY2UgPSBuZXcgQ3VzdG9tUmVzb3VyY2VJb1RUaGluZ0NlcnRQb2xpY3kodGhpcywgJ0NyZWF0ZVRoaW5nQ2VydFBvbGljeUN1c3RvbVJlc291cmNlJywge1xuICAgICAgZnVuY3Rpb25OYW1lOiBpZCArICctQ3JlYXRlVGhpbmdDZXJ0UG9saWN5RnVuY3Rpb24nLFxuICAgICAgc3RhY2tOYW1lOiBpZCxcbiAgICB9KTtcbiAgICBuZXcgY2RrLkNmbk91dHB1dCh0aGlzLCAnQ2VydGlmaWNhdGVQRU0nLCB7XG4gICAgICBkZXNjcmlwdGlvbjogJ0NlcnRpZmljYXRlIG9mIEdyZWVuZ3Jhc3MgQ29yZSB0aGluZycsXG4gICAgICB2YWx1ZTogY3JJb1RSZXNvdXJjZS5jZXJ0aWZpY2F0ZVBlbVxuICAgIH0pO1xuICAgIG5ldyBjZGsuQ2ZuT3V0cHV0KHRoaXMsICdQcml2YXRlS2V5UEVNJywge1xuICAgICAgZGVzY3JpcHRpb246ICdQcml2YXRlIEtleSBvZiBHcmVlbmdyYXNzIENvcmUgdGhpbmcnLFxuICAgICAgdmFsdWU6IGNySW9UUmVzb3VyY2UucHJpdmF0ZUtleVBlbVxuICAgIH0pO1xuXG4gICAgLy8gQ3JlYXRlIEdyZWVuZ3Jhc3MgU2VydmljZSByb2xlIHdpdGggcGVybWlzc2lvbnMgdGhlIENvcmUncyByZXNvdXJjZXMgc2hvdWxkIGhhdmVcbiAgICBuZXcgQ3VzdG9tUmVzb3VyY2VHcmVlbmdyYXNzU2VydmljZVJvbGUodGhpcywgXCJHcmVlbmdyYXNzUm9sZUN1c3RvbVJlc291cmNlXCIsIHtcbiAgICAgIGZ1bmN0aW9uTmFtZTogaWQgKyAnLUdyZWVuZ3Jhc3NSb2xlRnVuY3Rpb24nLFxuICAgICAgc3RhY2tOYW1lOiBpZCwgICAgICBcbiAgICAgIHJvbGVQb2xpY3k6IHtcbiAgICAgICAgXCJWZXJzaW9uXCI6IFwiMjAxMi0xMC0xN1wiLFxuICAgICAgICBcIlN0YXRlbWVudFwiOiB7XG4gICAgICAgICAgICBcIkVmZmVjdFwiOiBcIkFsbG93XCIsXG4gICAgICAgICAgICBcIkFjdGlvblwiOiBcImlvdDoqXCIsXG4gICAgICAgICAgICBcIlJlc291cmNlXCI6IFwiKlwiLFxuICAgICAgICB9XG4gICAgfSxcbiAgICB9KTtcblxuXG5cbiAgfVxufVxuXG4vLyBQcmUtc3RhY2sgY3JlYXRpb24gc3RlcHNcblxuLy8gQ3JlYXRlIHN0YWNrXG5jb25zdCBhcHAgPSBuZXcgY2RrLkFwcCgpO1xubmV3IEdyZWVuZ3Jhc3NTdHJlYW1NYW5hZ2VyU3RhY2soYXBwLCAnZ2ctc3RyZWFtLWFjY2VsJyk7XG5hcHAuc3ludGgoKTtcbiJdfQ==