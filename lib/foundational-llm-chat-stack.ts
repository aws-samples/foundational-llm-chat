import { SystemConfig } from "../bin/config";
import { Stack, StackProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import { Networking } from "./network";
import { ecsApplication } from "./ecs";
import { Cognito } from "./authentication";
import { CustomResources } from "./custom";
import { Parameters } from "./parameters";
import { Prompts } from "./prompts";


// Interface to define the properties for the FoundationalLlmChatStack
export interface FoundationalLlmChatStackProps extends StackProps {
  readonly config: SystemConfig;
}

export class FoundationalLlmChatStack extends Stack {
  constructor(scope: Construct, id: string, props: FoundationalLlmChatStackProps) {
    super(scope, id, props);

    const prompts = new Prompts(this, "Prompts", {
      bedrock_models: props.config.bedrock_models,
      default_system_prompt: props.config.default_system_prompt
    });

    // load Parameters from config file
    const parameters = new Parameters(this, "Parameters", {
      prefix: props.config.prefix, // Prefix from the configuration
      prompts_manager_list: prompts.promptsIdList,
      max_characters_parameter: props.config.max_characters_parameter,
      max_content_size_mb_parameter: props.config.max_content_size_mb_parameter,
      bedrock_models_parameter: props.config.bedrock_models
    });

    // Create an instance of the CustomResources construct
    const customResources = new CustomResources(this, "CustomResources", {
      prefix: props.config.prefix, // Prefix from the configuration
    });

    // Create an instance of the Networking construct
    const networking = new Networking(this, "Networking", {
      cloudFrontPrefixList: customResources.cloudFrontPrefixList, // Use the CloudFront prefix list from CustomResources
      prefix: props.config.prefix, // Prefix from the configuration
    });

    // Create an instance of the Cognito construct
    const cognito = new Cognito(this, "Cognito", {
      cloudFrontDistribution: networking.cloudFrontDistribution, // Use the CloudFront distribution from Networking
      prefix: props.config.prefix, // Prefix from the configuration
    });

    // Create an instance of the ecsApplication construct
    new ecsApplication(this, "ecsApplication", {
      region: props.config.default_aws_region,
      prompts_manager_list: prompts.promptsIdList, // list of prompt for getting the version arns
      vpc: networking.vpc, // Use the VPC from Networking
      clientIdParameter: cognito.clientIdParameter, // Use the client ID from Cognito
      cognitoDomainParameter: cognito.cognitoDomainParameter,
      publicLoadBalancer: networking.publicLoadBalancer, // Use the public load balancer from Networking
      cloudFrontDistributionURLParameter: networking.cloudFrontDistributionURLParameter, // Use the CloudFront distribution from Networking
      oauth_cognito_client_secret: cognito.oauth_cognito_client_secret, // Use the secrets from SecretsManager
      system_prompts_parameter: parameters.system_prompts_parameter, // System prompt from the configuration
      max_characters_parameter: parameters.max_characters_parameter, // Max number of char from the configuration
      max_content_size_mb_parameter: parameters.max_content_size_mb_parameter, // Max content size from the configuration
      bedrock_models_parameter: parameters.bedrock_models_parameter, // Models configuration from the configuration
      prefix: props.config.prefix, // Prefix from the configuration
      bedrockModels: props.config.bedrock_models, //models configured
      accountId: props.env?.account
    });
  }
}
