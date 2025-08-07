import { existsSync, readFileSync } from "fs";

export interface InferenceProfile {
  prefix: string;
  region: string;
}

export interface ReasoningConfig {
  enabled: boolean;
  hybrid?: boolean;
  budget_thinking_tokens?: boolean;
  temperature_forced?: number;
  send_back_reasoning_to_llm?: boolean;
  openai_reasoning_modalities?: boolean;
}

export interface BedrockModel {
  system_prompt?: string;
  id: string;
  inference_profile?: InferenceProfile;
  region?: string[];
  cost: {
    input_1k_price: number;
    output_1k_price: number;
  };
  default?: boolean;
  maxTokens: number;
  vision?: boolean;
  document?: boolean;
  tool?: boolean;
  reasoning?: boolean | ReasoningConfig;
  streaming?: boolean;
}

export interface BedrockModels {
  [key: string]: BedrockModel;
}

export interface SystemConfig {
  default_system_prompt: string;
  cognito_domain?: string;
  max_characters_parameter: string;
  max_content_size_mb_parameter: string;
  default_aws_region: string;
  prefix: string;
  bedrock_models: BedrockModels;
}


export function getConfig(): SystemConfig {
  if (existsSync("./bin/config.json")) {
    return JSON.parse(readFileSync("./bin/config.json").toString("utf8"));
  }

  // Default config
  return {
    default_system_prompt: "You are an assistant",
    max_characters_parameter: "None",
    max_content_size_mb_parameter: "None",
    default_aws_region: "us-west-2",
    prefix: "newv",
    bedrock_models: {
      "Claude Sonnet 3.5 New": {
        "id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "inference_profile": {
          "prefix": "us",
          "region": "us-west-2"
        },
        "region": ["us-east-1", "us-west-2", "us-east-2"],
        "cost": {
          "input_1k_price": 0.003,
          "output_1k_price": 0.015
        },
        "default": true,
        "maxTokens": 4096,
        "vision": true,
        "document": true,
        "tool": true,
        "reasoning": {
          "enabled": false
        },
        "streaming": true
      }
    }
  };
}

export const config: SystemConfig = getConfig();
