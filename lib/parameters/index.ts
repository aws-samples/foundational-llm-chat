import { Construct } from "constructs";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { BedrockModels } from "../../bin/config";
import { ModelPrompts } from "../prompts";

export interface ParametersProps {
  readonly max_characters_parameter: string;
  readonly max_content_size_mb_parameter: string;
  readonly bedrock_models_parameter: BedrockModels;
  readonly prefix: string;
  readonly prompts_manager_list: ModelPrompts;
}

export class Parameters extends Construct {
  public readonly system_prompts_parameter: ssm.StringParameter;
  public readonly max_characters_parameter: ssm.StringParameter;
  public readonly max_content_size_mb_parameter: ssm.StringParameter;
  public readonly bedrock_models_parameter: ssm.StringParameter;

  constructor(scope: Construct, id: string, props: ParametersProps) {
    super(scope, id);

    this.system_prompts_parameter = new ssm.StringParameter(this, "SystemPromptsParameter", {
      parameterName: `${props.prefix}system_prompts`,
      description: "JSON list of system prompts for each model",
      stringValue: JSON.stringify(props.prompts_manager_list),
      tier: ssm.ParameterTier.STANDARD,
    });

    this.max_characters_parameter = new ssm.StringParameter(this, "MaxCharactersParameter", {
      parameterName: `${props.prefix}max_characters_parameter`,
      description: "maximum number of characters per user prompt",
      stringValue: props.max_characters_parameter,
      tier: ssm.ParameterTier.STANDARD,
    });

    this.max_content_size_mb_parameter = new ssm.StringParameter(this, "MaxContentSizeMbParameter", {
      parameterName: `${props.prefix}max_content_size_mb_parameter`,
      description: "maximum dimension for content attached in chat in MB",
      stringValue: props.max_content_size_mb_parameter,
      tier: ssm.ParameterTier.STANDARD,
    });

    // Remove system_prompt field from bedrock_models_parameter
    const bedrock_models_without_system_prompts = Object.entries(props.bedrock_models_parameter).reduce((acc, [key, value]) => {
      const { system_prompt, ...rest } = value;
      acc[key] = rest;
      return acc;
    }, {} as BedrockModels);

    this.bedrock_models_parameter = new ssm.StringParameter(this, "BedrockModelsParameter", {
      parameterName: `${props.prefix}bedrock_models_parameter`,
      description: "available models with prices (excluding system prompts)",
      stringValue: JSON.stringify(bedrock_models_without_system_prompts),
      tier: ssm.ParameterTier.STANDARD,
    });
  }
}
