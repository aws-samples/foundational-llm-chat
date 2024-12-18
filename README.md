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
    - Claude 3 Opus
    - Claude 3 Sonnet
    - Claude 3 Haiku
    - Claude 3.5 Sonnet
  - 🦙 Meta Llama models:
    - Llama 3.1 (8B, 70B)
    - Llama 3.2 (1B, 3B, 11B Vision, 90B Vision)
  - 🌟 Mistral models
  - 🤖 Amazon Nova models
  - 🔵 AI21 Jurassic models
  - 🎯 Cohere Command models
  - And any new text generation model added to Amazon Bedrock
- 🖼️ Multi-modal capabilities (for vision-enabled models)
- 📄 Document analysis through Amazon Bedrock Converse API
- 🛠️ Tool integration capabilities through Converse API
- 🌍 Optional cross-region inference support
- 📝 Prompt management and versioning through Amazon Bedrock Prompt Manager
- 🔐 Secure authentication with AWS Cognito
- 🚀 Scalable deployment using AWS ECS and Fargate
- 🌐 Global distribution with AWS CloudFront
- 🔄 Sticky sessions for consistent user experience
- 💰 Detailed cost tracking for model usage
- 🎚️ Configure temperature, max tokens, and other settings

## Architecture

The application leverages several Amazon Bedrock features:
- Converse API for enhanced document and vision processing
- Cross-region inference using instance profiles
- Prompt management for versioning and governance
- Multi-model support across different providers

![Foundational LLM Chat Architecture](/assets/Foundational-LLM-Chat.svg)

The architecture diagram illustrates the AWS deployment of the Foundational LLM Chat application. Users interact with the application through a web interface secured by Amazon Cognito authentication. The application is globally distributed using Amazon CloudFront's CDN. Within a specific AWS region, the application is deployed across multiple Availability Zones using Amazon ECS for containerized deployment. The backend integrates with Amazon Bedrock to leverage various language models, enabling users to engage in multimodal conversations with the AI assistant.

## Configuration

The application is configured through a `config.json` file in the `./bin` folder. Key configuration options include:

### General Settings
1. **`default_system_prompt`**: This field contains the default system prompt that will be used by the chatbot if not specified below in the `bedrock_models` field. It defines the initial instructions and behavior of the AI assistant. You can modify this value to change the assistant's persona or initial prompt.

2. **`max_characters_parameter`**: This field specifies the maximum number of characters allowed in the input text. If set to the string `"None"`, there is no character limit. You can change this value to limit the input text length if desired.

3. **`max_content_size_mb_parameter`**: This field sets the maximum size of the input content (e.g., images) in megabytes. If set to the string `"None"`, there is no size limit. You can modify this value to restrict the maximum size of input content.

4. **`default_aws_region`**: This field specifies the AWS region where the application is deployed. You can set region also for each Amazon Bedrock model field.

5. **`prefix`**: This field allows you to set a prefix for resource names created by the application. You can leave it empty or provide a custom prefix if desired.

6. **`cognito_domain`**: This field allows you to specify an already existent cognito domain name. It is *optional* and in the first deployement is expected to not be defined. See FAQ section for the reason of this parameter existance.

### Model Configuration
This field contains a dictionary of Bedrock models that the chatbot can use. Each model is identified by a *key* (e.g., "Sonnet", "Haiku") and, the *key* is the name used in the Chainlit [Chatprofile](https://docs.chainlit.io/advanced-features/chat-profiles). Each model has the following properties at minimum:
   - **`id`**: The ID or ARN of the Amazon Bedrock model. You can find the available model IDs in the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html#model-ids-arns).
   - **`region`**: an array of regions used to access the model. One if you did not enable cross-region inference, multiple for cross region inference.

Optional configuration parameters include:
- `inference_profile`: Settings for cross-region inference
  - `prefix`: Region prefix (e.g., "us")
  - `region`: Primary inference region
  - Note: Required only when using cross-region inference. Models must be enabled in all specified regions
- `system_prompt`: Custom system prompt
- `cost`: Pricing information
  - **`input_1k_price`**: The cost (in USD) for 1,000 input tokens. You can find the pricing information for different models on the [AWS Bedrock pricing page](https://aws.amazon.com/bedrock/pricing/).
     - **`output_1k_price`**: The cost (in USD) for 1,000 output tokens.
- Capability flags:
   - **`vision`** *[optional]*: true or false. If vision capabilities [are enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) for the model.
   - **`document`** *[optional]*: true or false. If document capabilities are enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) for the model.
   - **`tool`** *[optional]*: true or false. If tools capabilities are enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) for the model.
- **`default`** *[optional]*: true or false. The default selected model

You can modify the `bedrock_models` section to include additional models or update the existing ones according to your requirements.

Here's an example of how to retrieve the model ID and pricing information:

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
      "default": true,
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

you can edit the `extract_and_process_prompt` function inside `chainlit_image/foundational-llm-chat_app/massages_utils.py` to add more direct substitutions.

## Amazon Bedrock Integration

### Converse API
The application uses Amazon Bedrock's Converse API, providing:
- Unified interface for all Amazon Bedrock models
- Built-in support for multi-modal interactions
- Document processing capabilities
- Tool integration framework

### Cross-Region Support
- Optional cross-region inference configuration
- Requires model enablement in all specified regions
- Configurable through inference profiles in config.json

### Prompt Management
All system prompts are stored and managed through Amazon Bedrock Prompt Manager, offering:
- Version control and history
- Extended prompt length limits
- Centralized management across applications
- Easy updates and rollbacks

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
8. [AWS CDK CLI](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) installed
9. [Finch](https://github.com/runfinch/finch) installed or [Docker](https://www.docker.com/) installed

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

3. *\[Optional only if you did not not done it before in the deployment region\]* Bootstrap the CDK environment:

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

4. After the deployment is complete, the CloudFront distribution URL will be displayed in the terminal. Use this URL to access the foundational-llm-chat application.

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

1. *Self sign up is not enabled in this AWS Sample* so you need to add manually the user to you Amazon Cognito user pool to allow them to access the application. Open the AWS console and navigate to Amazon Cognito. You find a User Pool named: `foundational-llm-chat-user-pool`. Open this user pool and create a user also verifing the email address;
2. Open the Foundational LLM Chat application in your web browser using the CloudFront distribution URL;
3. Sign up or sign in using the AWS Cognito authentication flow;
4. Select the desired chat profile to interact with the corresponding model;
5. Type your message or upload supported content (images/documents) in the chat input area;
6. Adjust settings like system prompt, temperature, max tokens, and cost display as needed;
7. View the multimodal responses from the model;
8. Use this sample as a fast starting point for building demo/project based on Generative AI on a chatbot console.

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
1) what if I get: `failed: The stack named STACKNAME failed to deploy: UPDATE_ROLLBACK_COMPLETE: User pool already has a domain configured. (Service: AWSCognitoIdentityProviderService; Status Code: 400; Error Code: InvalidParameterException; Request ID: ID; Proxy: null)`?
This is due to the following reason: https://github.com/aws/aws-cdk/issues/10062, so if you add to your config.json the optional field: "cognito_domain" with the already deployed cognito domain. You can find it inside parameter store in a parameter named: "prefixCognitoDomainName". Here an example: `databranchfoundational-llm-chat9778.auth.us-west-2.amazoncognito.com`.

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
