"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const cfn = require("@aws-cdk/aws-cloudformation");
const lambda = require("@aws-cdk/aws-lambda");
const iam = require("@aws-cdk/aws-iam");
const cdk = require("@aws-cdk/core");
const uuid = require("uuid/v5");
class CustomResourceGreengrassServiceRole extends cdk.Construct {
    constructor(scope, id, props) {
        super(scope, id);
        props.physicalId = props.functionName;
        // IAM role name
        props.roleName = props.stackName + "-GreengrassGroupRole";
        new cfn.CustomResource(this, 'Resource', {
            provider: cfn.CustomResourceProvider.fromLambda(new lambda.SingletonFunction(this, 'Singleton', {
                functionName: props.functionName,
                uuid: uuid(props.functionName, uuid.DNS),
                code: lambda.Code.fromAsset('cr-greengrass-service-role/cr_greengrass_service_role'),
                handler: 'index.main',
                timeout: cdk.Duration.seconds(30),
                runtime: lambda.Runtime.PYTHON_3_8,
                initialPolicy: [
                    new iam.PolicyStatement({
                        actions: ['iam:CreateRole', 'iam:DeleteRole', 'iam:AttachRolePolicy',
                            'iam:PutRolePolicy', 'iam:ListRolePolicies', 'iam:DeleteRolePolicy', 'iam:ListAttachedRolePolicies',
                            'iam:DetachRolePolicy',
                        ],
                        resources: ['*']
                    })
                ]
            })),
            properties: props
        });
    }
}
exports.CustomResourceGreengrassServiceRole = CustomResourceGreengrassServiceRole;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY3ItZ3JlZW5ncmFzcy1zZXJ2aWNlLXJvbGUuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyJjci1ncmVlbmdyYXNzLXNlcnZpY2Utcm9sZS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBLG1EQUFvRDtBQUNwRCw4Q0FBK0M7QUFDL0Msd0NBQXlDO0FBQ3pDLHFDQUFzQztBQUV0QyxnQ0FBaUM7QUFnQmpDLE1BQWEsbUNBQW9DLFNBQVEsR0FBRyxDQUFDLFNBQVM7SUFDcEUsWUFBWSxLQUFvQixFQUFFLEVBQVUsRUFBRSxLQUErQztRQUMzRixLQUFLLENBQUMsS0FBSyxFQUFFLEVBQUUsQ0FBQyxDQUFDO1FBQ2pCLEtBQUssQ0FBQyxVQUFVLEdBQUcsS0FBSyxDQUFDLFlBQVksQ0FBQztRQUN0QyxnQkFBZ0I7UUFDaEIsS0FBSyxDQUFDLFFBQVEsR0FBRyxLQUFLLENBQUMsU0FBUyxHQUFHLHNCQUFzQixDQUFBO1FBRXpELElBQUksR0FBRyxDQUFDLGNBQWMsQ0FBQyxJQUFJLEVBQUUsVUFBVSxFQUFFO1lBQ3ZDLFFBQVEsRUFBRSxHQUFHLENBQUMsc0JBQXNCLENBQUMsVUFBVSxDQUFDLElBQUksTUFBTSxDQUFDLGlCQUFpQixDQUFDLElBQUksRUFBRSxXQUFXLEVBQUU7Z0JBQzlGLFlBQVksRUFBRSxLQUFLLENBQUMsWUFBWTtnQkFDaEMsSUFBSSxFQUFFLElBQUksQ0FBQyxLQUFLLENBQUMsWUFBWSxFQUFFLElBQUksQ0FBQyxHQUFHLENBQUM7Z0JBQ3hDLElBQUksRUFBRSxNQUFNLENBQUMsSUFBSSxDQUFDLFNBQVMsQ0FBQyx1REFBdUQsQ0FBQztnQkFDcEYsT0FBTyxFQUFFLFlBQVk7Z0JBQ3JCLE9BQU8sRUFBRSxHQUFHLENBQUMsUUFBUSxDQUFDLE9BQU8sQ0FBQyxFQUFFLENBQUM7Z0JBQ2pDLE9BQU8sRUFBRSxNQUFNLENBQUMsT0FBTyxDQUFDLFVBQVU7Z0JBQ2xDLGFBQWEsRUFBRTtvQkFDYixJQUFJLEdBQUcsQ0FBQyxlQUFlLENBQUM7d0JBQ3RCLE9BQU8sRUFBRSxDQUFDLGdCQUFnQixFQUFFLGdCQUFnQixFQUFFLHNCQUFzQjs0QkFDbEUsbUJBQW1CLEVBQUUsc0JBQXNCLEVBQUUsc0JBQXNCLEVBQUUsOEJBQThCOzRCQUNuRyxzQkFBc0I7eUJBQ3ZCO3dCQUNELFNBQVMsRUFBRSxDQUFDLEdBQUcsQ0FBQztxQkFDakIsQ0FBQztpQkFBQzthQUNOLENBQUMsQ0FBQztZQUNILFVBQVUsRUFBRSxLQUFLO1NBQ2xCLENBQUMsQ0FBQztJQUNMLENBQUM7Q0FDRjtBQTNCRCxrRkEyQkMiLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgY2ZuID0gcmVxdWlyZSgnQGF3cy1jZGsvYXdzLWNsb3VkZm9ybWF0aW9uJyk7XG5pbXBvcnQgbGFtYmRhID0gcmVxdWlyZSgnQGF3cy1jZGsvYXdzLWxhbWJkYScpO1xuaW1wb3J0IGlhbSA9IHJlcXVpcmUoJ0Bhd3MtY2RrL2F3cy1pYW0nKTtcbmltcG9ydCBjZGsgPSByZXF1aXJlKCdAYXdzLWNkay9jb3JlJyk7XG5cbmltcG9ydCB1dWlkID0gcmVxdWlyZSgndXVpZC92NScpO1xuXG5leHBvcnQgaW50ZXJmYWNlIEN1c3RvbVJlc291cmNlR3JlZW5ncmFzc1NlcnZpY2VSb2xlUHJvcHMge1xuICAvKipcbiAgICogUmVzb3VyY2UgcHJvcGVydGllcyB1c2VkIHRvIGNvbnN0cnVjdCB0aGUgY3VzdG9tIHJlc291cmNlIGFuZCBwYXNzZWQgYXMgZGljdGlvbmFyeVxuICAgKiB0byB0aGUgcmVzb3VyY2UgYXMgcGFydCBvZiB0aGUgXCJSZXNvdXJjZVByb3BlcnRpZXNcIi4gTm90ZSB0aGF0IHRoZSBwcm9wZXJ0aWVzIGJlbG93XG4gICAqIHdpbGwgaGF2ZSBhbiB1cHBlcmNhc2UgZmlyc3QgY2hhcmFjdGVyIGFuZCB0aGUgcmVzdCBvZiB0aGUgcHJvcGVydHkga2VwdCBpbnRhY3QuXG4gICAqIEZvciBleGFtcGxlLCBwaHlzaWNhbElkIHdpbGwgYmUgcGFzc2VkIGFzIFBoeXNpY2FsSWRcbiAgICovXG4gIGZ1bmN0aW9uTmFtZTogc3RyaW5nO1xuICBzdGFja05hbWU6IHN0cmluZztcbiAgcm9sZVBvbGljeTogb2JqZWN0O1xuICByb2xlTmFtZT86IHN0cmluZztcbiAgcGh5c2ljYWxJZD86IHN0cmluZztcbn1cblxuZXhwb3J0IGNsYXNzIEN1c3RvbVJlc291cmNlR3JlZW5ncmFzc1NlcnZpY2VSb2xlIGV4dGVuZHMgY2RrLkNvbnN0cnVjdCB7XG4gIGNvbnN0cnVjdG9yKHNjb3BlOiBjZGsuQ29uc3RydWN0LCBpZDogc3RyaW5nLCBwcm9wczogQ3VzdG9tUmVzb3VyY2VHcmVlbmdyYXNzU2VydmljZVJvbGVQcm9wcykge1xuICAgIHN1cGVyKHNjb3BlLCBpZCk7XG4gICAgcHJvcHMucGh5c2ljYWxJZCA9IHByb3BzLmZ1bmN0aW9uTmFtZTtcbiAgICAvLyBJQU0gcm9sZSBuYW1lXG4gICAgcHJvcHMucm9sZU5hbWUgPSBwcm9wcy5zdGFja05hbWUgKyBcIi1HcmVlbmdyYXNzR3JvdXBSb2xlXCJcblxuICAgIG5ldyBjZm4uQ3VzdG9tUmVzb3VyY2UodGhpcywgJ1Jlc291cmNlJywge1xuICAgICAgcHJvdmlkZXI6IGNmbi5DdXN0b21SZXNvdXJjZVByb3ZpZGVyLmZyb21MYW1iZGEobmV3IGxhbWJkYS5TaW5nbGV0b25GdW5jdGlvbih0aGlzLCAnU2luZ2xldG9uJywge1xuICAgICAgICBmdW5jdGlvbk5hbWU6IHByb3BzLmZ1bmN0aW9uTmFtZSxcbiAgICAgICAgdXVpZDogdXVpZChwcm9wcy5mdW5jdGlvbk5hbWUsIHV1aWQuRE5TKSxcbiAgICAgICAgY29kZTogbGFtYmRhLkNvZGUuZnJvbUFzc2V0KCdjci1ncmVlbmdyYXNzLXNlcnZpY2Utcm9sZS9jcl9ncmVlbmdyYXNzX3NlcnZpY2Vfcm9sZScpLFxuICAgICAgICBoYW5kbGVyOiAnaW5kZXgubWFpbicsXG4gICAgICAgIHRpbWVvdXQ6IGNkay5EdXJhdGlvbi5zZWNvbmRzKDMwKSxcbiAgICAgICAgcnVudGltZTogbGFtYmRhLlJ1bnRpbWUuUFlUSE9OXzNfOCxcbiAgICAgICAgaW5pdGlhbFBvbGljeTogW1xuICAgICAgICAgIG5ldyBpYW0uUG9saWN5U3RhdGVtZW50KHtcbiAgICAgICAgICAgIGFjdGlvbnM6IFsnaWFtOkNyZWF0ZVJvbGUnLCAnaWFtOkRlbGV0ZVJvbGUnLCAnaWFtOkF0dGFjaFJvbGVQb2xpY3knLFxuICAgICAgICAgICAgICAnaWFtOlB1dFJvbGVQb2xpY3knLCAnaWFtOkxpc3RSb2xlUG9saWNpZXMnLCAnaWFtOkRlbGV0ZVJvbGVQb2xpY3knLCAnaWFtOkxpc3RBdHRhY2hlZFJvbGVQb2xpY2llcycsXG4gICAgICAgICAgICAgICdpYW06RGV0YWNoUm9sZVBvbGljeScsXG4gICAgICAgICAgICBdLFxuICAgICAgICAgICAgcmVzb3VyY2VzOiBbJyonXVxuICAgICAgICAgIH0pXVxuICAgICAgfSkpLFxuICAgICAgcHJvcGVydGllczogcHJvcHNcbiAgICB9KTtcbiAgfVxufVxuXG4iXX0=