import { Construct } from "constructs";
import * as ssm from "aws-cdk-lib/aws-ssm";


// sample of config file which is used to get the parameters by this component
/* {
  "system_prompt": "You are an assistant.",
  "max_characters_parameter": "None",
  "max_content_size_mb_parameter": "None",
  "aws_region": "us-west-2",
  "prefix": "",
  "bedrock_models": {
    "Haiku": {
      "id": "anthropic.claude-3-haiku-20240307-v1:0",
      "cost": {
        "input_1k_price": 0.00025,
        "output_1k_price": 0.00125
      }
    },
    "Sonnet": {
      "id": "anthropic.claude-3-sonnet-20240229-v1:0",
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.015
      }
    }
  }
} */


// Interface to define the properties required for the ECS Application construct
export interface parametersProps {
  readonly system_prompt: string;
  readonly max_characters_parameter: string;
  readonly max_content_size_mb_parameter: string;
  readonly bedrock_models_parameter: { [key: string]: { id: string, cost: { input_1k_price: number, output_1k_price: number } } };
}

export class Parameters extends Construct {
  public readonly system_prompt_parameter: ssm.StringParameter;
  public readonly max_characters_parameter: ssm.StringParameter;
  public readonly max_content_size_mb_parameter: ssm.StringParameter;
  public readonly bedrock_models_parameter: ssm.StringParameter;

  constructor(scope: Construct, id: string, props: parametersProps) {
    super(scope, id);

    this.system_prompt_parameter = new ssm.StringParameter(this, "SystemPromptParameter", {
      parameterName: "system_prompt",
      description: "System prompt for chainlit",
      stringValue: props.system_prompt,
      tier: ssm.ParameterTier.ADVANCED, // for 8k maximum payload
    });

    this.max_characters_parameter = new ssm.StringParameter(this, "MaxCharactersParameter", {
      parameterName: "max_characters_parameter",
      description: "maximum number of characters per user prompt",
      stringValue: props.max_characters_parameter,
      tier: ssm.ParameterTier.STANDARD,
    });

    this.max_content_size_mb_parameter = new ssm.StringParameter(this, "MaxContentSizeMbParameter", {
      parameterName: "max_content_size_mb_parameter",
      description: "maximum dimension for content attached in chat in MB",
      stringValue: props.max_content_size_mb_parameter,
      tier: ssm.ParameterTier.STANDARD,
    });

    this.bedrock_models_parameter = new ssm.StringParameter(this, "BedrockModelsParameter", {
      parameterName: "bedrock_models_parameter",
      description: "available models with prices",
      stringValue: JSON.stringify(props.bedrock_models_parameter),
      tier: ssm.ParameterTier.STANDARD,
    });

  }
}
