import { Duration } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecsPatterns from "aws-cdk-lib/aws-ecs-patterns";
import * as iam from "aws-cdk-lib/aws-iam";
import { DockerImageAsset } from "aws-cdk-lib/aws-ecr-assets";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as logs from "aws-cdk-lib/aws-logs";
import { BedrockModels, BedrockModel } from "../../bin/config";
import { ModelPrompts } from "../prompts";


// Interface to define the properties required for the ECS Application construct
export interface ecsApplicationProps {
  readonly region: string;
  readonly vpc: ec2.Vpc;
  readonly clientIdParameter: ssm.StringParameter;
  readonly cognitoDomainParameter: ssm.StringParameter;
  readonly publicLoadBalancer: elbv2.ApplicationLoadBalancer;
  readonly oauth_cognito_client_secret: secretsmanager.Secret;
  readonly cloudFrontDistributionURLParameter: ssm.StringParameter;
  readonly system_prompts_parameter: ssm.StringParameter;
  readonly max_characters_parameter: ssm.StringParameter;
  readonly max_content_size_mb_parameter: ssm.StringParameter;
  readonly bedrock_models_parameter: ssm.StringParameter;
  readonly prefix: string;
  readonly bedrockModels: BedrockModels;
  readonly accountId?: string;
  readonly prompts_manager_list: ModelPrompts;
}

export class ecsApplication extends Construct {
  public readonly service: ecsPatterns.ApplicationLoadBalancedFargateService;

  constructor(scope: Construct, id: string, props: ecsApplicationProps) {
    super(scope, id);

    // Store the client secret
    const authCodeSecret = new secretsmanager.Secret(this, "authCodeChainlitSecret", {
      secretName: `${props.prefix}chainlit_auth_secret`,
      description: "Secret nedeed by chainlit",
      generateSecretString: {
        passwordLength: 64,
      },
    });

    // Create a Docker image asset from the local directory
    const image = new DockerImageAsset(this, "chainlit_image", {
      directory: "./chainlit_image",
    });

    // Create an ECS cluster
    const ecsCluster = new ecs.Cluster(this, "FoundationalLlmChatCluster", { vpc: props.vpc });

    // Create a Fargate service and configure it with the Docker image, environment variables, and other settings
    this.service = new ecsPatterns.ApplicationLoadBalancedFargateService(this, "FoundationalLlmChatService", {
      cluster: ecsCluster,
      taskImageOptions: {
        image: ecs.ContainerImage.fromDockerImageAsset(image),
        containerPort: 8080,
        logDriver: ecs.LogDrivers.awsLogs({
          streamPrefix: `${props.prefix}FoundationalLlmChatServiceECSLogs`,
          logRetention: logs.RetentionDays.FIVE_DAYS
        }),
        environment: {
          AWS_REGION: props.region ? props.region : "us-west-2",
        },
        secrets: {
          OAUTH_COGNITO_CLIENT_SECRET: ecs.Secret.fromSecretsManager(props.oauth_cognito_client_secret),
          CHAINLIT_AUTH_SECRET: ecs.Secret.fromSecretsManager(authCodeSecret),
          OAUTH_COGNITO_DOMAIN: ecs.Secret.fromSsmParameter(props.cognitoDomainParameter),
          OAUTH_COGNITO_CLIENT_ID: ecs.Secret.fromSsmParameter(props.clientIdParameter),
          CHAINLIT_URL: ecs.Secret.fromSsmParameter(props.cloudFrontDistributionURLParameter),
          SYSTEM_PROMPT_LIST: ecs.Secret.fromSsmParameter(props.system_prompts_parameter),
          MAX_CHARACTERS: ecs.Secret.fromSsmParameter(props.max_characters_parameter),
          MAX_CONTENT_SIZE_MB: ecs.Secret.fromSsmParameter(props.max_content_size_mb_parameter),
          BEDROCK_MODELS: ecs.Secret.fromSsmParameter(props.bedrock_models_parameter),
        },
      },
      taskSubnets: { subnets: props.vpc.privateSubnets },
      loadBalancer: props.publicLoadBalancer,
      openListener: false,
      memoryLimitMiB: 1024,
      cpu: 512,
      desiredCount: 2,
      runtimePlatform: {
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
      },
      capacityProviderStrategies: [
        {
          capacityProvider: "FARGATE", // all container with fargate spot is not advided for production, use FARGATE instead or a mix with FARGATE_SPOT
          base: 1,
          weight: 1,
        },
      ],
    });

    const generateArns = (model: BedrockModel, defaultRegion: string, accountId: string) => {
      const arns: string[] = [];

      // Handle region list
      if (Array.isArray(model.region)) {
        model.region.forEach(region => {
          const modelId = model.inference_profile ? model.id.replace(`${model.inference_profile.prefix}.`, '') : model.id;
          arns.push(`arn:aws:bedrock:${region}::foundation-model/${modelId}`);
        });
      } else {
        // If no region list, use the default region
        arns.push(`arn:aws:bedrock:${defaultRegion}::foundation-model/${model.id}`);
      }

      // Handle inference_profile
      if (model.inference_profile) {
        arns.push(`arn:aws:bedrock:${model.inference_profile.region}:${accountId}:inference-profile/${model.id}`);
      }

      return arns;
    };

    // Generate the resource ARNs
    const resourceArns = Object.values(props.bedrockModels).flatMap(model =>
      generateArns(model, props.region || "us-west-2", props.accountId || "*")
    );

    // Allow the ECS task to call the Bedrock API
    this.service.taskDefinition.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: resourceArns,
        actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      })
    );

    // Generate ARNs for the prompts
    const promptArns = Object.values(props.prompts_manager_list).map(prompt =>
      `${prompt.arn}`
    );

    // Allow the ECS task to get the prompts
    this.service.taskDefinition.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: promptArns,
        actions: ["bedrock:GetPrompt"],
      })
    );

    // Enable sticky sessions for the Fargate service
    this.service.targetGroup.enableCookieStickiness(Duration.days(1));
  }
}
