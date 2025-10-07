import { existsSync, readFileSync } from "fs";

export interface InferenceProfile {
  prefix: string;
  region: string;
  global?: boolean;
}

/**
 * Reasoning configuration for models that support thinking/reasoning capabilities.
 *
 * Supports two formats:
 * 1. Simple boolean: true/false - Enables/disables standard Anthropic-style reasoning
 * 2. Extended object with detailed configuration options
 */
export interface ReasoningConfig {
  enabled: boolean;
  /**
   * Enables OpenAI-style reasoning behavior (uses effort levels instead of token budgets)
   * When true, the UI shows reasoning effort selector (low/medium/high)
   * When false or omitted, the UI shows token budget slider
   */
  openai_reasoning_modalities?: boolean;
  /**
   * Prevents sending ANY reasoning parameters to the API
   * Use this for models where reasoning is always enabled at the model level
   * and cannot be controlled via API parameters (e.g., DeepSeek R1)
   * When true, the app will:
   * - Show reasoning in the UI (always on, no toggle)
   * - NOT send any additionalModelRequestFields for reasoning
   * - Still process reasoningContent from the response
   */
  no_reasoning_params?: boolean;
  /**
   * Supports hybrid reasoning modes (Anthropic-specific)
   */
  hybrid?: boolean;
  /**
   * Supports configurable token budgets for thinking process (Anthropic-specific)
   */
  budget_thinking_tokens?: boolean;
  /**
   * Forces specific temperature when reasoning is enabled (Anthropic-specific)
   * Typically set to 1 to allow full model creativity during reasoning
   */
  temperature_forced?: number;
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
  streaming?: boolean;
  /**
   * Reasoning/thinking capability configuration.
   *
   * Can be:
   * - boolean: true/false for simple enable/disable (standard Anthropic-style)
   * - ReasoningConfig object: for detailed configuration with multiple options
   *
   * Examples:
   * - "reasoning": false - No reasoning support
   * - "reasoning": true - Standard Anthropic reasoning with token budgets
   * - "reasoning": { "enabled": true, "openai_reasoning_modalities": true } - OpenAI-style with effort levels
   * - "reasoning": { "enabled": true, "hybrid": true, "budget_thinking_tokens": true, "temperature_forced": 1 } - Full Anthropic config
   */
  reasoning?: boolean | ReasoningConfig;
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
        id: "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        inference_profile: {
          prefix: "us",
          region: "us-west-2",
        },
        region: ["us-east-1", "us-west-2", "us-east-2"],
        cost: {
          input_1k_price: 0.003,
          output_1k_price: 0.015,
        },
        default: true,
        maxTokens: 4096,
        vision: true,
        document: true,
        tool: true,
        streaming: true,
        reasoning: false,
      },
    },
  };
}

export const config: SystemConfig = getConfig();
