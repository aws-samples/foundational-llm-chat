import { CustomResource } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import * as customResources from "aws-cdk-lib/custom-resources";
import { Duration } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";

// Interface to define the properties required for the CustomResources construct
export interface CustomResourcesProps {
  readonly prefix: string,
}

export class CustomResources extends Construct {
  public readonly cloudFrontPrefixList: string;

  constructor(scope: Construct, id: string, props: CustomResourcesProps) {
    super(scope, id);

    // Create a Lambda function to get the CloudFront prefix list
    const getCloudFrontPrefixList = new lambda.Function(this, 'getCloudFrontPrefixList', {
      code: lambda.Code.fromAsset("./custom_resources/lambda/cloudFront_get_prefix_list"),
      handler: 'cloudFront_get_prefix_list.handler',
      runtime: lambda.Runtime.PYTHON_3_12,
      timeout: Duration.seconds(300),
      memorySize: 128,
      logGroup: new logs.LogGroup(this,  `${props.prefix}getCloudFrontPrefixListLogs`, {
        retention: logs.RetentionDays.ONE_DAY,
      })
    });

    // Add an IAM policy statement to allow the Lambda function to describe managed prefix lists
    getCloudFrontPrefixList.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        "ec2:DescribeManagedPrefixLists"
      ],
      resources: ["*"]
    }));

    // Create a custom resource provider to invoke the Lambda function
    const lambdagetCloudFrontPrefixListProvider = new customResources.Provider(this, 'lambdagetCloudFrontPrefixListProvider', {
      onEventHandler: getCloudFrontPrefixList,
    });

    // Create a custom resource to get the CloudFront prefix list from the Lambda function
    const lambdagetCloudFrontPrefixListResult = new CustomResource(this, 'lambdagetCloudFrontPrefixListResult', {
      serviceToken: lambdagetCloudFrontPrefixListProvider.serviceToken,
    });

    // Get the authentication code and CloudFront prefix list from the custom resources
    this.cloudFrontPrefixList = lambdagetCloudFrontPrefixListResult.getAttString("prefix_lists")
  }
}
