import cfn = require("@aws-cdk/aws-cloudformation")
import lambda = require("@aws-cdk/aws-lambda")
import iam = require("@aws-cdk/aws-iam")
import cdk = require("@aws-cdk/core")

import { v5 as uuidv5 } from "uuid"

export interface CustomResourceGreengrassManageDeploymentsProps {
  /**
   * Automates the deployment or deployment reset whenever the underlying
   * Greengrass group is modified via CloudFormation/CDK.
   */
  functionName: string
  stackName: string
  greengrassGroupName: string
  // Used for detecting changes when using InitialVersion
  greengrassGroupId: string
  // Required only when using groupVersion
  greengrassGroupVersionId?: string
  physicalId?: string
}

export class CustomResourceGreengrassManageDeployments extends cdk.Construct {
  public readonly roleArn: string
  // public resource: cfn.CustomResource;

  constructor(
    scope: cdk.Construct,
    id: string,
    props: CustomResourceGreengrassManageDeploymentsProps
  ) {
    super(scope, id)
    props.physicalId = props.functionName

    new cfn.CustomResource(this, "Resource", {
      provider: cfn.CustomResourceProvider.fromLambda(
        new lambda.SingletonFunction(this, "Singleton", {
          functionName: props.functionName,
          uuid: uuidv5(props.functionName, uuidv5.DNS),
          code: lambda.Code.fromAsset(
            "cr-greengrass-manage-deployments/cr_greengrass_manage_deployments"
          ),
          handler: "index.main",
          timeout: cdk.Duration.seconds(30),
          runtime: lambda.Runtime.PYTHON_3_8,
          initialPolicy: [
            new iam.PolicyStatement({
              actions: ["greengrass:*", "iot:*"],
              resources: ["*"],
            }),
          ],
        })
      ),
      properties: props,
    })
  }
}
