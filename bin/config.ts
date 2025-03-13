import { existsSync, readFileSync } from "fs";

export interface InferenceProfile {
  prefix: string;
  region: string;
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
  vision?: boolean;
  document?: boolean;
  tool?: boolean;
  reasoning?: boolean;
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
    "Claude Opus": {
      "id": "us.anthropic.claude-3-opus-20240229-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.015,
        "output_1k_price": 0.075
      },
      "vision": true,
      "document": true,
      "tool": true,
      "reasoning": false
    },
    "Claude Sonnet": {
      "id": "us.anthropic.claude-3-sonnet-20240229-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.015
      },
      "default": false,
      "vision": true,
      "document": true,
      "tool": true,
      "reasoning": false
    },
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
      "vision": true,
      "document": true,
      "tool": true,
      "reasoning": false
    },
    "Claude Sonnet 3.5": {
      "id": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.015
      },
      "vision": true,
      "document": true,
      "tool": true,
      "reasoning": false
    },
    "Claude Haiku": {
      "id": "us.anthropic.claude-3-haiku-20240307-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.00025,
        "output_1k_price": 0.00125
      },
      "vision": true,
      "document": true,
      "tool": true,
      "reasoning": false
    },
    "Mistral Large 2": {
      "id": "mistral.mistral-large-2407-v1:0",
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.009
      },
      "vision": false,
      "document": true,
      "tool": true
    },
    "Meta Llama 3.1 8B": {
      "id": "meta.llama3-1-8b-instruct-v1:0",
      "cost": {
        "input_1k_price": 0.0003,
        "output_1k_price": 0.0006
      },
      "vision": false,
      "document": true,
      "tool": true
    },
    "Meta Llama 3.1 70B": {
      "id": "meta.llama3-1-70b-instruct-v1:0",
      "cost": {
        "input_1k_price": 0.00265,
        "output_1k_price": 0.0035
      },
      "vision": false,
      "document": true,
      "tool": true
    },
    "Meta Llama 3.2 1B Instruct": {
      "id": "us.meta.llama3-2-1b-instruct-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.0001,
        "output_1k_price": 0.0001
      },
      "vision": false,
      "document": true,
      "tool": true
    },
    "Meta Llama 3.2 3B Instruct": {
      "id": "us.meta.llama3-2-3b-instruct-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.00015,
        "output_1k_price": 0.00015
      },
      "vision": false,
      "document": true,
      "tool": true
    },
    "Meta Llama 3.2 11B Vision Instruct": {
      "id": "us.meta.llama3-2-11b-instruct-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.00035,
        "output_1k_price": 0.00035
      },
      "vision": true,
      "document": true,
      "tool": true
    },
    "Meta Llama 3.2 90B Vision Instruct": {
      "id": "us.meta.llama3-2-90b-instruct-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-east-1", "us-west-2"],
      "cost": {
        "input_1k_price": 0.002,
        "output_1k_price": 0.002
      },
      "vision": true,
      "document": true,
      "tool": true
    }
  }
};
}

export const config: SystemConfig = getConfig();
