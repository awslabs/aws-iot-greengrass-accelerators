import cfn = require("@aws-cdk/aws-cloudformation")
import lambda = require("@aws-cdk/aws-lambda")
import iam = require("@aws-cdk/aws-iam")
import cdk = require("@aws-cdk/core")

import { v5 as uuidv5 } from "uuid"

export interface CustomResourceS3DeleteObjectsProps {
  /**
   * Resource properties used to construct the custom resource and passed as dictionary
   * to the resource as part of the "ResourceProperties". Note that the properties below
   * will have an uppercase first character and the rest of the property kept intact.
   * For example, physicalId will be passed as PhysicalId
   */
  functionName: string
  stackName: string
  bucketName: string
  roleName?: string
  physicalId?: string
}

export class CustomResourceS3DeleteObjects extends cdk.Construct {
  constructor(
    scope: cdk.Construct,
    id: string,
    props: CustomResourceS3DeleteObjectsProps
  ) {
    super(scope, id)
    props.physicalId = props.functionName
    // IAM role name
    props.roleName = props.stackName + "-S3DeleteObjectsRole"

    new cfn.CustomResource(this, "Resource", {
      provider: cfn.CustomResourceProvider.fromLambda(
        new lambda.SingletonFunction(this, "Singleton", {
          functionName: props.functionName,
          uuid: uuidv5(props.functionName, uuidv5.DNS),
          code: lambda.Code.fromAsset(
            "cr-s3-delete-objects/cr_s3_delete_objects"
          ),
          handler: "index.main",
          timeout: cdk.Duration.seconds(30),
          runtime: lambda.Runtime.PYTHON_3_8,
          initialPolicy: [
            new iam.PolicyStatement({
              actions: [
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:ListBucketVersions",
                "s3:DeleteBucket",
              ],
              resources: ["arn:aws:s3:::" + props.bucketName],
            }),
            new iam.PolicyStatement({
              actions: [
                "s3:List*",
                "s3:DeleteObject",
                "s3:DeleteObjectVersion",
              ],
              resources: ["arn:aws:s3:::" + props.bucketName + "/*"],
            }),
          ],
        })
      ),
      properties: props,
    })
  }
}
