import { Duration, CfnOutput } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as s3 from "aws-cdk-lib/aws-s3";
import { RemovalPolicy } from 'aws-cdk-lib';
import * as ssm from "aws-cdk-lib/aws-ssm";

// Interface to define the properties required for the Networking construct
export interface NetworkingProps {
  readonly cloudFrontPrefixList: string;
  readonly prefix: string, // Prefix from the configuration
}

export class Networking extends Construct {
  public readonly vpc: ec2.Vpc;
  public readonly publicLoadBalancer: elbv2.ApplicationLoadBalancer;
  public readonly cloudFrontDistribution: cloudfront.Distribution;
  public readonly cloudFrontDistributionURLParameter: ssm.StringParameter;

  constructor(scope: Construct, id: string, props: NetworkingProps) {
    super(scope, id);

    // Create a new VPC with public, private with egress, and private isolated subnets
    this.vpc = new ec2.Vpc(this, "foundationalLlmChat-vpc", {
      vpcName: `${props.prefix}foundationalLlmChat-vpc`,
      maxAzs: 2,
      subnetConfiguration: [
        {
          name: "public-subnet",
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: "private-subnet-ecs",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
        {
          name: "isolated-subnet-rds",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
      natGateways: 1,
    });

    // create a flow log to be associated with VPC and that sends logs in Cloudwatch
    // this is a best practice but not strictly required
    this.vpc.addFlowLog('FlowLogCloudWatchfoundationalLlmChatVpc', {
      destination: ec2.FlowLogDestination.toCloudWatchLogs(),
    });

    // Create a security group for the application
    const foundationalLlmChatAppSecurityGroup = new ec2.SecurityGroup(this, "foundationalLlmChatAppSecurityGroup", {
      vpc: this.vpc,
      description: "foundationalLlmChat is internet exposed",
      allowAllOutbound: true,
    });

    // Add an ingress rule to allow access to the container from CloudFront
    foundationalLlmChatAppSecurityGroup.addIngressRule(
      ec2.Peer.prefixList(props.cloudFrontPrefixList),
      ec2.Port.tcp(80),
      "allow 80 access from cloudfront"
    );

    // create a bucket for enabling load balancer and distribution logs logs
    const logBucket = new s3.Bucket(this, 'foundationalLlmChatLogsBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: false,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      serverAccessLogsPrefix: "bucket-access-logs",
      objectOwnership: s3.ObjectOwnership.OBJECT_WRITER
    });

    // Create a public Application Load Balancer
    this.publicLoadBalancer = new elbv2.ApplicationLoadBalancer(this, "foundationalLlmChatPublicLoadBalancer", {
      vpc: this.vpc,
      internetFacing: true,
      vpcSubnets: { subnets: this.vpc.publicSubnets },
      securityGroup: foundationalLlmChatAppSecurityGroup
    });
    // enabling logs
    this.publicLoadBalancer.logAccessLogs(logBucket, "ApplicationLoadBalancerLogs");

    // Create a sticky cache policy for CloudFront for the public load balancer (AWSALB*) with a minimum TTL of 1 second.
    // This will ensure that the same user always gets the same response. This is useful for implementing sticky sessions.
    const stickyCachePolicy = new cloudfront.CachePolicy(this, "stickyCachePolicy", {
      cookieBehavior: cloudfront.CacheCookieBehavior.allowList("AWSALB*"),
      enableAcceptEncodingGzip: true,
      enableAcceptEncodingBrotli: true,
      minTtl: Duration.seconds(1),
    });

    // Create a CloudFront distribution
    // This will serve the public load balancer as the origin for the CloudFront distribution.
    // The cache policy is set to the sticky cache policy created above.
    // The origin request policy is set to "ALL_VIEWER_EXCEPT_HOST_HEADER" to ensure that the host header is not sent to the origin.
    // The allowed methods are set to "ALLOW_ALL" to allow all HTTP methods.
    // The viewer protocol policy is set to "REDIRECT_TO_HTTPS" to redirect all HTTP requests to HTTPS.
    this.cloudFrontDistribution = new cloudfront.Distribution(this, 'foundationalLlmChat_distribution', {
      defaultBehavior: {
        origin: new origins.LoadBalancerV2Origin(this.publicLoadBalancer, { protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY }),
        cachePolicy: stickyCachePolicy,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      enableLogging: true,
      logBucket: logBucket,
      logFilePrefix: "CloudFrontLogs",
    });

    const ddname = `https://${this.cloudFrontDistribution.distributionDomainName}`
    this.cloudFrontDistributionURLParameter = new ssm.StringParameter(this, 'cf_distribution_url', {
      description: 'Cloudfront Distribution URL',
      parameterName: `${props.prefix}CloudfrontDistributionURL`,
      stringValue: ddname,
      tier: ssm.ParameterTier.STANDARD,
    });


    // Create a CloudFormation output with the CloudFront distribution domain name
    new CfnOutput(this, 'FoundationalLlmChatDNS', {
      value: `https://${this.cloudFrontDistribution.distributionDomainName}`,
      description: 'DNS name of the your distribution, use it to access to your application',
    });
  }
}
