[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Foundational LLM Chat: A Chainlit App for Interacting with Amazon Bedrock LLMs

Foundational LLM Chat is a Chainlit application built using AWS CDK and Converse API that allows you to interact with Amazon Bedrock language model. It provides a user-friendly interface to chat with Amazon Bedrock LLMs, upload **images or docuements**, and receive multimodal responses. The application is deployed on AWS using various services like Amazon Bedrock, Amazon Elastic Container Service, Amazon Cognito, Amazon CloudFront, and more.

<img src="/assets/app.gif"/>

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Before Deployment Customization](#before-deployment-customization)
  - [Security Considerations and Prompt Injection](#security-considerations-and-prompt-injection)
  - [Prompt Engineering](#prompt-engineering)
    - [Beginner](#beginner)
    - [Intermediate](#intermediate)
    - [Advanced](#advanced)
- [Deploy with AWS Cloud9](#deploy-with-aws-cloud9)
- [Local Deployment](#local-deployment)
  - [Prerequisites](#prerequisites)
  - [Deployment](#deployment)
- [Usage](#usage)
- [Clean Up](#clean-up)
- [FAQ] (#faq)
- [Production Deployment Considerations](#production-deployment-considerations)
  - [Secure Communication with HTTPS](#secure-communication-with-https)
  - [General Disclaimer](#general-disclaimer)
- [Contributing](#contributing)
- [License](#license)
- [Legal Disclaimer](#legal-disclaimer)

## Features

- 🌐 Support for all text generation models in Amazon Bedrock through Converse API, including:
  - 🤖 Anthropic Claude models:
    - Claude Opus 4, Claude Sonnet 4, Claude Sonnet 4.5
    - Claude 3 Opus, Claude 3 Sonnet, Claude 3.5 Sonnet
    - Claude 3.7 Sonnet (with extended thinking capabilities)
    - Claude 3 Haiku, Claude 3.5 Haiku, Claude Haiku 4.5
  - 🦙 Meta Llama models:
    - Llama 3.1 (8B, 70B), Llama 3.2 (1B, 3B, 11B Vision, 90B Vision), Llama 3.3 (70B)
    - Llama 4 (Scout, Maverick variants)
  - 🌟 Mistral models (including Pixtral Large with vision)
  - 🤖 Amazon Nova models (Micro, Lite, Pro, Premier)
  - 🧠 DeepSeek models (V3, R1 with reasoning)
  - 🔵 Qwen models (multiple variants including Coder)
  - ✍️ Writer Palmyra models
  - 🔓 OpenAI GPT OSS models
  - And any new text generation model added to Amazon Bedrock
- 🖼️ Multi-modal capabilities (for vision-enabled models)
- 🧠 Dual reasoning approaches:
  - Standard thinking process (Anthropic-style with token budgets)
  - OpenAI-style reasoning (with effort levels: low/medium/high)
- 📄 Document analysis through Amazon Bedrock Converse API
- 🛠️ MCP (Model Context Protocol) integration for tool calling
- 🌍 Cross-region inference and global inference profiles support
- 📝 Prompt management and versioning through Amazon Bedrock Prompt Manager
- 🔐 Secure authentication with AWS Cognito
- 🚀 Scalable deployment using AWS ECS and Fargate
- 🌐 Global distribution with AWS CloudFront
- 🔄 Sticky sessions for consistent user experience
- 💰 Detailed cost tracking for model usage
- 🎚️ Configure temperature, max tokens, reasoning budget/effort, and other settings
- 🔄 Support for both streaming and non-streaming modes (configurable per model)

## Architecture

The application leverages several Amazon Bedrock features:

- Converse API for enhanced document and vision processing
- Cross-region inference using inference profiles
- Global inference profiles for worldwide model access
- Prompt Manager for centralized prompt versioning and governance
- Multi-model support across different providers

![Foundational LLM Chat Architecture](/assets/Foundational-LLM-Chat.svg)

The architecture diagram illustrates the AWS deployment of the Foundational LLM Chat application. Users interact with the application through a web interface secured by Amazon Cognito authentication. The application is globally distributed using Amazon CloudFront's CDN. Within a specific AWS region, the application is deployed across multiple Availability Zones using Amazon ECS for containerized deployment. The backend integrates with Amazon Bedrock to leverage various language models, enabling users to engage in multimodal conversations with the AI assistant. All system prompts are managed through Amazon Bedrock Prompt Manager for version control and centralized management.

## Configuration

The application is configured through a `config.json` file in the `./bin` folder. Key configuration options include:

### General Settings

1. **`default_system_prompt`**: This field contains the default system prompt that will be used by the chatbot if not specified below in the `bedrock_models` field. It defines the initial instructions and behavior of the AI assistant. You can modify this value to change the assistant's persona or initial prompt.

2. **`max_characters_parameter`**: This field specifies the maximum number of characters allowed in the input text. If set to the string `"None"`, there is no character limit. You can change this value to limit the input text length if desired.

3. **`max_content_size_mb_parameter`**: This field sets the maximum size of the input content (e.g., images) in megabytes. If set to the string `"None"`, there is no size limit. You can modify this value to restrict the maximum size of input content.

4. **`default_aws_region`**: This field specifies the AWS region where the application is deployed. You can set region also for each Amazon Bedrock model field.

5. **`prefix`**: This field allows you to set a prefix for resource names created by the application. You can leave it empty or provide a custom prefix if desired.

6. **`cognito_domain`**: This field allows you to _optionally_ specify a pre-existing [Cognito domain name](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-assign-domain.html). If left blank (by default) a new domain will be generated for you automatically.

### Model Configuration

This field contains a dictionary of Bedrock models that the chatbot can use. Each model is identified by a _key_ (e.g., "Sonnet", "Haiku") and, the _key_ is the name used in the Chainlit [Chatprofile](https://docs.chainlit.io/advanced-features/chat-profiles). Each model has the following properties at minimum:

- **`id`**: The ID or ARN of the Amazon Bedrock model. You can find the available model IDs in the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html#model-ids-arns).
- **`region`**: an array of regions used to access the model. One if you did not enable cross-region inference, multiple for cross region inference.

Optional configuration parameters include:

- `inference_profile`: Settings for cross-region or global inference
  - `prefix`: Region prefix (e.g., "us") or "global" for global inference profiles
  - `region`: Primary inference region
  - `global`: _[optional]_ Set to `true` for global inference profiles (e.g., `global.anthropic.claude-sonnet-4-5-20250929-v1:0`)
  - Note: Required only when using cross-region or global inference. Models must be enabled in all specified regions
- `system_prompt`: Custom system prompt (overrides default_system_prompt for this model)
- `cost`: Pricing information
  - **`input_1k_price`**: The cost (in USD) for 1,000 input tokens. You can find the pricing information for different models on the [AWS Bedrock pricing page](https://aws.amazon.com/bedrock/pricing/).
  - **`output_1k_price`**: The cost (in USD) for 1,000 output tokens.
- Capability flags:
  - **`vision`** _[optional]_: true or false. If vision capabilities [are enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) for the model.
  - **`document`** _[optional]_: true or false. If document capabilities [are enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) for the model.
  - **`tool`** _[optional]_: true or false. If tools capabilities [are enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) for the model.
  - **`streaming`** _[optional]_: true or false. If streaming is supported for the model. Defaults to true if not specified.
  - **`reasoning`** _[optional]_: Configures thinking/reasoning capabilities. Supports three formats:
    - **Boolean `false`**: Disables reasoning completely (default for most models)
    - **Boolean `true`**: Enables standard Anthropic-style reasoning with token budgets
    - **Extended object**: Detailed configuration with the following properties:
      - `"enabled": true` - **Required** when using object format. Whether reasoning is supported
      - `"openai_reasoning_modalities": true` - _[optional]_ Enables OpenAI-style reasoning behavior:
        - Uses reasoning effort levels (low/medium/high) instead of token budgets
        - Automatically sets temperature and top_p to 1.0
        - Only includes thinking in conversation history when tools are used
        - Used by models like DeepSeek V3, OpenAI GPT OSS, and some Qwen models
      - `"no_reasoning_params": true` - _[optional]_ Prevents sending ANY reasoning parameters to the API:
        - Use for models where reasoning is always enabled at the model level (e.g., DeepSeek R1)
        - The app will NOT send additionalModelRequestFields for reasoning
        - Reasoning will still be displayed in the UI (always on, no toggle)
        - The app will still process reasoningContent from the response
        - Must be combined with `"openai_reasoning_modalities": true` for proper response handling
      - `"hybrid": true` - _[optional]_ Supports hybrid reasoning modes (Anthropic-specific)
      - `"budget_thinking_tokens": true` - _[optional]_ Supports configurable token budgets for thinking (Anthropic-specific)
      - `"temperature_forced": 1` - _[optional]_ Forces specific temperature when reasoning is enabled (typically 1 for full creativity)
- **`maxTokens`** _[optional]_: Maximum tokens the model can generate. Used to set the slider range in the UI.
- **`default`** _[optional]_: true or false. The default selected model

You can modify the `bedrock_models` section to include additional models or update the existing ones according to your requirements.

### Reasoning Parameter Examples

The `reasoning` parameter controls how models handle thinking/reasoning processes. Here are real-world examples from the configuration:

#### No Reasoning Support

Most models don't support reasoning and should have `"reasoning": false`:

```json
"Claude 3.5 Haiku": {
  "id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "reasoning": false
}
```

#### Simple Anthropic-Style Reasoning

For models that support basic Anthropic thinking with token budgets, use `"reasoning": true`:

```json
"DeepSeek R1": {
  "id": "us.deepseek.r1-v1:0",
  "reasoning": true
}
```

This enables:

- Token budget slider (1024-64000 tokens)
- Thinking always included in conversation history
- Temperature disabled when thinking is active

#### Advanced Anthropic-Style Reasoning

For Claude models with extended thinking capabilities:

```json
"Claude 3.7 Sonnet": {
  "id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
  "reasoning": {
    "enabled": true,
    "hybrid": true,
    "budget_thinking_tokens": true,
    "temperature_forced": 1
  }
}
```

This enables:

- Token budget slider with hybrid mode support
- Interleaved thinking option (beta) for tool calls
- Temperature forced to 1 during reasoning
- Full thinking context in conversation history

#### OpenAI-Style Reasoning

For models using OpenAI's reasoning approach (DeepSeek V3, OpenAI GPT OSS, Qwen models):

```json
"DeepSeek V3": {
  "id": "deepseek.v3-v1:0",
  "tool": false,
  "reasoning": {
    "enabled": true,
    "openai_reasoning_modalities": true
  }
}
```

This enables:

- Reasoning effort selector (low/medium/high) instead of token budget
- Temperature and top_p automatically set to 1.0
- Thinking only included in history when tools are used
- Always-on reasoning (no toggle in UI)

#### Model-Level Reasoning (Always On)

For models where reasoning is built-in and cannot be controlled via API (DeepSeek R1):

```json
"DeepSeek R1": {
  "id": "us.deepseek.r1-v1:0",
  "tool": false,
  "reasoning": {
    "enabled": true,
    "openai_reasoning_modalities": true,
    "no_reasoning_params": true
  }
}
```

This configuration:

- Tells the app reasoning is always enabled at the model level
- Prevents sending ANY reasoning parameters to the API (avoids validation errors)
- Still displays reasoning in the UI (always on, no toggle)
- Processes `reasoningContent` from the response correctly
- Uses OpenAI-style response handling (separate reasoning and text blocks)

**Note**: Models with `"openai_reasoning_modalities": true` may have `"tool": false` if they require specific tool configurations that would force tool usage in all scenarios.

### Model ID and Pricing Information

Here's how to retrieve the model ID and pricing information:

1. To find the model ID or ARN, refer to the [AWS Bedrock Model IDs documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html#model-ids-arns). For example, the ID for the Claude 3 Sonnet model is `anthropic.claude-3-sonnet-20240229-v1:0`.

2. To find the pricing information, refer to the [AWS Bedrock Pricing documentation](https://aws.amazon.com/bedrock/pricing/). For the Claude 3 Sonnet model, the input and output pricing is as follows:
   - Input: $0.003 per 1,000 tokens
   - Output: $0.015 per 1,000 tokens

After making the desired changes to the `config.json` file, you can proceed with the deployment as described in the README.

Here an example of the json:

```json
{
  "default_system_prompt": "you are an assistant",
  "max_characters_parameter": "None",
  "max_content_size_mb_parameter": "None",
  "default_aws_region": "us-west-2",
  "prefix": "",
  "bedrock_models": {
    "Claude 3.7 Sonnet": {
      "system_prompt": "you are an assistant",
      "id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
      "inference_profile": {
        "prefix": "us",
        "region": "us-west-2"
      },
      "region": ["us-west-2", "us-east-1", "us-east-2"],
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.015
      },
      "default": true,
      "maxTokens": 64000,
      "vision": true,
      "document": true,
      "tool": true,
      "streaming": true,
      "reasoning": {
        "enabled": true,
        "hybrid": true,
        "budget_thinking_tokens": true,
        "temperature_forced": 1
      }
    },
    "Claude Sonnet 4.5 (Global)": {
      "id": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
      "inference_profile": {
        "prefix": "global",
        "region": "us-west-2",
        "global": true
      },
      "region": [
        "us-east-1",
        "us-west-2",
        "us-east-2",
        "eu-west-1",
        "ap-southeast-1"
      ],
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.015
      },
      "maxTokens": 64000,
      "vision": true,
      "document": true,
      "tool": true,
      "reasoning": {
        "enabled": true,
        "hybrid": true,
        "budget_thinking_tokens": true,
        "temperature_forced": 1
      }
    },
    "DeepSeek V3": {
      "id": "deepseek.v3-v1:0",
      "region": ["us-west-2"],
      "cost": {
        "input_1k_price": 0.0008,
        "output_1k_price": 0.0032
      },
      "maxTokens": 8192,
      "vision": false,
      "document": true,
      "tool": false,
      "streaming": true,
      "reasoning": {
        "enabled": true,
        "openai_reasoning_modalities": true
      }
    },
    "Claude Sonnet 3.5 New": {
      "system_prompt": "you are an assistant",
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
      "maxTokens": 8192,
      "vision": true,
      "document": true,
      "tool": true,
      "streaming": true
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
      "maxTokens": 4096,
      "vision": true,
      "document": true,
      "tool": true,
      "streaming": true
    },
    "Mistral Large 2": {
      "id": "mistral.mistral-large-2407-v1:0",
      "region": ["us-west-2"],
      "cost": {
        "input_1k_price": 0.003,
        "output_1k_price": 0.009
      },
      "maxTokens": 4096,
      "vision": false,
      "document": true,
      "tool": true,
      "streaming": true
    }
  }
}
```

### Prompt Management

The application leverages Amazon Bedrock Prompt Manager for:

- Version control of prompts
- Higher length limits for prompts
- Centralized prompt management
- Simplified prompt deployment and updates

## Prompt Replacement

Currently the application supports 2 automatic variable substitutions:

- {{TODAY}}: will be replaced with `%Y-%m-%d` of the day;
- {{UTC_TIME}}: will be replaced with `%Y-%m-%d %H:%M:%S UTC`

you can edit the `extract_and_process_prompt` function inside `chainlit_image/foundational-llm-chat_app/utils/message_utils.py` to add more direct substitutions.

## Amazon Bedrock Integration

### Converse API

The application uses Amazon Bedrock's Converse API, providing:

- Unified interface for all Amazon Bedrock models
- Built-in support for multi-modal interactions
- Document processing capabilities
- Tool integration framework

### Cross-Region and Global Inference

Amazon Bedrock offers two types of inference profiles for enhanced availability and performance:

#### Cross-Region Inference Profiles

- Route requests across multiple regions within a geographic area (e.g., "us" prefix for US regions)
- Provides automatic failover and load balancing
- Requires model enablement in all specified regions
- Example: `us.anthropic.claude-3-7-sonnet-20250219-v1:0` routes across US regions

#### Global Inference Profiles

- Route requests across AWS regions worldwide for maximum availability
- Ideal for production workloads requiring high uptime
- Uses "global" prefix in model ID
- Example: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Requires model access in all regions listed in the `region` array

Configuration in `config.json`:

```json
"inference_profile": {
  "prefix": "global",  // or "us", "eu", etc.
  "region": "us-west-2",  // Primary region for API calls
  "global": true  // Set to true for global profiles
}
```

### MCP (Model Context Protocol) Integration

The application supports MCP for tool calling capabilities:

- Connect to MCP servers to extend model functionality
- Automatic tool discovery and registration
- Seamless integration with Bedrock Converse API
- Support for multiple concurrent MCP connections
- Tools are automatically available to models with `"tool": true` capability

### Prompt Management

All system prompts are stored and managed through Amazon Bedrock Prompt Manager, offering:

- Version control and history tracking
- Extended prompt length limits (up to 200KB)
- Centralized management across applications
- Easy updates and rollbacks without code changes
- Automatic variable substitution ({{TODAY}}, {{UTC_TIME}})
- Prompts are created during CDK deployment and retrieved at runtime

### Security Considerations and Prompt Injection

When using system prompts to configure the behavior of language models, it's crucial to consider security implications and take measures to prevent potential misuse or vulnerabilities. One significant risk is **prompt injection**, where malicious inputs could manipulate the system prompt in unintended ways, potentially leading to harmful or biased outputs.

A good starting point is the following guide: [Mitigating jailbreaks & prompt injections](https://docs.anthropic.com/claude/docs/mitigating-jailbreaks-prompt-injections).

### Prompt Engineering

Prompt engineering refers to the practice of carefully crafting prompts or instructions to guide language models in generating the desired outputs. Effective prompt engineering is crucial for ensuring that language models understand and respond appropriately to the given context and task.

The following course is intended to provide you with a comprehensive step-by-step understanding of how to engineer optimal prompts within Claude, using Bedrock: [Prompt Engineering with Anthropic Claude v3](https://github.com/aws-samples/prompt-engineering-with-anthropic-claude-v-3/tree/main).

This guide covers various techniques and best practices for prompt engineering through a series of lessons and exercises, organized into three levels: Beginner, Intermediate, and Advanced.

#### Beginner

- Chapter 1: Basic Prompt Structure
- Chapter 2: Being Clear and Direct
- Chapter 3: Assigning Roles

#### Intermediate

- Chapter 4: Separating Data from Instructions
- Chapter 5: Formatting Output & Speaking for Claude
- Chapter 6: Precognition (Thinking Step by Step)
- Chapter 7: Using Examples

#### Advanced

- Chapter 8: Avoiding Hallucinations
- Chapter 9: Building Complex Prompts (Industry Use Cases)
  - Complex Prompts from Scratch - Chatbot
  - Complex Prompts for Legal Services
  - Exercise: Complex Prompts for Financial Services
  - Exercise: Complex Prompts for Coding
  - Congratulations & Next Steps
- Appendix: Beyond Standard Prompting
  - Chaining Prompts
  - Tool Use
  - Search & Retrieval

By following the principles and techniques outlined in this guide, you can enhance the performance and reliability of your language model applications, ensuring that the AI assistant generates more relevant, coherent, and context-aware responses.

## Deploy with AWS Cloud9

We recommend deploying with [AWS Cloud9](https://aws.amazon.com/cloud9/).
If you'd like to use Cloud9 to deploy the solution, you will need the following before proceeding:

- select at least `m5.large` as Instance type.
- use `Amazon Linux 2023` as the platform.

## Local Deployment

If you have decided not to use AWS Cloud9, verify that your environment satisfies the following prerequisites:

### Prerequisites

Verify that your environment satisfies the following prerequisites:

You have:

1. An [AWS account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)
2. An access policy that allows you to create resources contained in the AWS Sample
3. Both console and programmatic access
4. [NodeJS lts](https://nodejs.org/en/download/) installed
   - If you are using [`nvm`](https://github.com/nvm-sh/nvm) you can run the following before proceeding
   - ```
     nvm install --lts
     ```

5. [NPM lts](https://www.npmjs.com/) installed
   - If you are using [`nvm`](https://github.com/nvm-sh/nvm) you can run the following before proceeding
   - ```
     nvm install-latest-npm
     ```

6. [AWS CLI](https://aws.amazon.com/cli/) installed and configured to use with your AWS account
7. [AWS CDK CLI](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) installed
8. [Finch](https://github.com/runfinch/finch) installed or [Docker](https://www.docker.com/) installed

### Deployment

1. Enable Amazon Bedrock models access in the deployment region:
   [How to enable Amazon Bedrock model access.](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

   Enable at least one of:
   - Claude 3 Opus
   - Claude 3 Sonnet
   - Claude 3 Haiku
   - Claude 3.5 Sonnet

2. Clone the repository, open the folder, install dependencies:

   ```bash
   git clone https://github.com/aws-samples/foundational-llm-chat.git
   cd foundational-llm-chat
   npm install
   ```

3. _\[Optional only if you did not not done it before in the deployment region\]_ Bootstrap the CDK environment:

   ```bash
   cdk bootstrap
   ```

4. Build and deploy the stack:

   ```bash
   cdk deploy --region YOUR_DEPLOY_REGION
   ```

   where YOUR_DEPLOY_REGION is the AWS region which you would like to deploy the application. For example: `us-west-2`.

   If you are using [Finch](https://github.com/runfinch/finch) instead of [Docker](https://www.docker.com/) please add `CDK_DOCKER=finch` at the begin of the command like in the following example:

   ```bash
   CDK_DOCKER=finch cdk deploy --region us-west-2
   ```

   This will create all the necessary resources on AWS, including the ECS cluster, Cognito user pool, CloudFront distribution, and more.

5. After the deployment is complete, the CloudFront distribution URL will be displayed in the terminal. Use this URL to access the foundational-llm-chat application.

## Usage

After the deployment you will get something similar to this:

```bash
 ✅  Foundational-LLM-ChatStack

✨  Deployment time: 465.09s

Outputs:
FoundationalLlmChatStack.CognitoUserPool = ID
FoundationalLlmChatStack.NetworkingFoundationalLlmChatChatbotStack = CLOUDFRONT_DISTRIBUTION_ADDRESS
FoundationalLlmChatStack.ecsApplicationFoundationalLlmChatServiceLoadBalancer = ECS_LOAD_BALANCER
FoundationalLlmChatStack.ecsApplicationFoundationalLlmChatServiceServiceURL = ECS_LOAD_BALANCER_ADDRESS
Stack ARN: ARN

✨  Total time: 469.14s
```

The Amazon CloudFront distribution is indicated in the following line: `FoundationalLlmChatStack.NetworkingFoundationalLlmChat = CLOUDFRONT_DISTRIBUTION_ADDRESS`

1. _Self sign up is not enabled in this AWS Sample_ so you need to add manually the user to you Amazon Cognito user pool to allow them to access the application. Open the AWS console and navigate to Amazon Cognito. You find a User Pool named: `foundational-llm-chat-user-pool`. Open this user pool and create a user also verifing the email address;
2. Open the Foundational LLM Chat application in your web browser using the CloudFront distribution URL;
3. Sign up or sign in using the AWS Cognito authentication flow;
4. Select the desired chat profile to interact with the corresponding model;
5. Type your message or upload supported content (images/documents) in the chat input area;
6. Adjust settings like system prompt, temperature, max tokens, thinking options (for supported models), and cost display as needed;
7. View the multimodal responses and thinking process (if enabled) from the model;
8. Use this sample as a fast starting point for building demo/project based on Generative AI on a chatbot console.

### Thinking/Reasoning Process

The application supports two distinct reasoning approaches based on the model type:

#### Standard Thinking (Anthropic-Style)

For models configured with `"reasoning": true` or `"reasoning": {"enabled": true}`:

**UI Controls**:

- Toggle thinking on/off using the "Enable Thinking Process" switch
- Adjustable reasoning budget (token limit for thinking process, 1024-64000 tokens)
- Temperature control is automatically disabled when thinking is enabled
- "Interleaved Thinking" beta feature for Claude models with tool calls (allows thinking between tool executions)

**Behavior**:

- Thinking content is **always** included in conversation history
- Supports signatures in reasoning content
- Works in both streaming and non-streaming modes
- Thinking is displayed as a separate "Thinking 🤔" step in the UI

**Configuration Example**:

```json
"Claude 3.7 Sonnet": {
  "id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
  "reasoning": {
    "enabled": true,
    "hybrid": true,
    "budget_thinking_tokens": true,
    "temperature_forced": 1
  }
}
```

#### OpenAI-Style Reasoning

For models configured with `"reasoning": {"enabled": true, "openai_reasoning_modalities": true}`:

**UI Controls**:

- Thinking is **always enabled** (no toggle available)
- Reasoning effort selector (low/medium/high) instead of token budget
- Temperature and top_p are automatically set to 1.0
- No interleaved thinking option

**Behavior**:

- Thinking content is **only** included in conversation history when tool calls are made
- No signature support in reasoning content
- For simple conversations without tools, reasoning is shown in UI but excluded from history
- This prevents conversation history bloat while preserving reasoning context for complex interactions

**Configuration Example**:

```json
"DeepSeek V3": {
  "id": "deepseek.v3-v1:0",
  "tool": false,
  "reasoning": {
    "enabled": true,
    "openai_reasoning_modalities": true
  }
}
```

**Note**: Models with OpenAI-style reasoning may have `"tool": false` if they require specific tool choice configurations that would force tool usage in all scenarios.

## Clean Up

To avoid incurring unnecessary costs, it's recommended to clean up and delete the resources created by this sample when you're done using them. Follow these steps to delete the stack and associated resources:

1. Open the AWS CloudFormation console.
2. Navigate to the stack named `Foundational-LLM-ChatStack`.
3. Select the stack and choose the "Delete" option.
4. Confirm the deletion when prompted.

This will delete the entire stack, including the ECS cluster, Cognito user pool, CloudFront distribution, and all other associated resources.

Alternatively, you can use the AWS CDK to delete the stack from the command line:

```bash
cdk destroy --region YOUR_DEPLOY_REGION
```

Replace `YOUR_DEPLOY_REGION` with the AWS region where you deployed the application.

Note that deleting the stack will not automatically delete the CloudWatch logs and Amazon ECS task definition created during the deployment. You may want to manually delete these resources if you no longer need them to avoid incurring additional costs.

## FAQ

1. **What if I get: `failed: The stack named STACKNAME failed to deploy: UPDATE_ROLLBACK_COMPLETE: User pool already has a domain configured`?**

   This is due to the following reason: https://github.com/aws/aws-cdk/issues/10062, so if you add to your config.json the optional field: "cognito_domain" with the already deployed cognito domain. You can find it inside parameter store in a parameter named: "prefixCognitoDomainName". Here an example: `databranchfoundational-llm-chat9778.auth.us-west-2.amazoncognito.com`.

2. **Where are MCP (Model Context Protocol) connections stored? How are they different for different users?**

   MCP connections are stored **client-side** in each user's browser session, not on the server. Here's how it works:
   - **Session-Based Storage**: Each user has their own isolated Chainlit session with a 15-day timeout
   - **Per-User Isolation**: MCP connections are stored in `cl.user_session` and are completely isolated between users
   - **No Server-Side Storage**: MCP connections are NOT stored in ECS containers, DynamoDB, or S3
   - **User-Specific**: Each user can connect to different MCP servers from their client
   - **Security**: User A cannot access User B's MCP tools - complete separation

   When a user connects an MCP server:
   1. The connection is established from their browser/client
   2. Tools are discovered and stored in their session (`@on_mcp_connect`)
   3. Tools are available only for that user's requests
   4. Connection is cleaned up when the session ends (`@on_mcp_disconnect`)

   For more information about MCP and Chainlit sessions, see the [Chainlit documentation](https://docs.chainlit.io/get-started/overview).

## Production Deployment Considerations

While the current architecture provides a good starting point for deploying the Foundational LLM Chat application, there are additional considerations for a production-ready deployment:

### Secure Communication with HTTPS

In the current architecture, communication between the CloudFront distribution and the Application Load Balancer (ALB) is over HTTP. For a production deployment, it is strongly recommended to use HTTPS (TLS/SSL) for secure communication:

1. **ALB TLS Termination**: Implement TLS termination on the ALB to secure the communication between CloudFront and the ALB. Note that the ALB already has a security group configured to allow incoming traffic only from the AWS CloudFront distribution's prefix list for HTTP traffic.
2. **ECS Task TLS Termination**: Implement TLS termination on the ECS tasks to secure the communication between the ALB and the ECS tasks.

Enabling HTTPS with TLS termination at both levels (ALB and ECS tasks) ensures end-to-end encryption and enhances the security of the application.

### General Disclaimer

This AWS Sample is intended for demonstration and educational purposes only. It is not designed for production use without further modifications and hardening. Before deploying this application to a production environment, it is crucial to conduct thorough testing, security assessments, and optimizations based on your specific requirements and best practices.

System prompts for claude can be obtained directly from Anthropic documentation here: [System Prompts](https://docs.anthropic.com/en/release-notes/system-prompts)

## Contributing

Contributions are welcome! Please follow the usual Git workflow:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Commit your changes
4. Push to the branch
5. Create a new pull request

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

- [License](LICENSE) of the project.
- [Code of Conduct](CODE_OF_CONDUCT.md) of the project.
- [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## Legal Disclaimer

You should consider doing your own independent assessment before using the content in this sample for production purposes. This may include (amongst other things) testing, securing, and optimizing the content provided in this sample, based on your specific quality control practices and standards.
