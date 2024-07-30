import { Construct } from "constructs";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { BedrockModels } from "../../bin/config";


// Interface to define the properties required for the ECS Application construct
export interface parametersProps {
  readonly system_prompt: string;
  readonly max_characters_parameter: string;
  readonly max_content_size_mb_parameter: string;
  readonly bedrock_models_parameter: BedrockModels;
  readonly prefix: string, // Prefix from the configuration
}

export class Parameters extends Construct {
  public readonly system_prompt_parameter: ssm.StringParameter;
  public readonly max_characters_parameter: ssm.StringParameter;
  public readonly max_content_size_mb_parameter: ssm.StringParameter;
  public readonly bedrock_models_parameter: ssm.StringParameter;

  constructor(scope: Construct, id: string, props: parametersProps) {
    super(scope, id);

    this.system_prompt_parameter = new ssm.StringParameter(this, "SystemPromptParameter", {
      parameterName: `${props.prefix}system_prompt`,
      description: "default system prompt for chainlit",
      stringValue: props.system_prompt,
      tier: ssm.ParameterTier.ADVANCED, // for 8k maximum payload
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

    this.bedrock_models_parameter = new ssm.StringParameter(this, "BedrockModelsParameter", {
      parameterName: `${props.prefix}bedrock_models_parameter`,
      description: "available models with prices",
      stringValue: JSON.stringify(props.bedrock_models_parameter),
      tier: ssm.ParameterTier.ADVANCED,
    });

  }
}
