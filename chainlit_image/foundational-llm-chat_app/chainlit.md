[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Foundational LLM Chat: A Chainlit App for Interacting with Claude LLM

Foundational LLM Chat is a Chainlit application built using AWS CDK that allows you to interact with Anthropic's Claude language model. It provides a user-friendly interface to chat with Claude, upload images, and receive multimodal responses. The application is deployed on AWS using various services like Amazon Bedrock, Amazon Elastic Container Service, Amazon Cognito, Amazon CloudFront, and more.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
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
- [Production Deployment Considerations](#production-deployment-considerations)
  - [Secure Communication with HTTPS](#secure-communication-with-https)
  - [General Disclaimer](#general-disclaimer)
- [Contributing](#contributing)
- [License](#license)
- [Legal Disclaimer](#legal-disclaimer)


## Features

- 🌐 Interact with Claude LLM using text and images
- 🔐 Secure authentication with AWS Cognito
- 🚀 Scalable deployment using AWS ECS and Fargate
- 🌐 Global distribution with AWS CloudFront
- 🔄 Sticky sessions for consistent user experience
- 💰 Cost tracking for model usage
- 🎚️ Configure temperature, max tokens, and other settings

## Architecture
![Foundational LLM Chat Architecture](/assets/Foundational-LLM-Chat.svg)

The architecture diagram illustrates the AWS deployment of the Foundational LLM Chat application. Users interact with the application through a web interface secured by Amazon Cognito authentication. The application is globally distributed using Amazon CloudFront's CDN. Within a specific AWS region, the application is deployed across multiple Availability Zones using Amazon ECS for containerized deployment. The backend integrates with Amazon Bedrock to leverage Anthropic's Claude language model, enabling users to engage in multimodal conversations with the AI assistant.

## Before deployment customization

Before deploying the application, you can customize various settings by modifying the `config.json` file located in the `./bin` folder. Here's an explanation of each field in the `config.json` file:

1. **`system_prompt`**: This field contains the system prompt that will be used by the chatbot. It defines the initial instructions and behavior of the AI assistant. You can modify this value to change the assistant's persona or initial prompt.

2. **`max_characters_parameter`**: This field specifies the maximum number of characters allowed in the input text. If set to the string `"None"`, there is no character limit. You can change this value to limit the input text length if desired.

3. **`max_content_size_mb_parameter`**: This field sets the maximum size of the input content (e.g., images) in megabytes. If set to the string `"None"`, there is no size limit. You can modify this value to restrict the maximum size of input content.

4. **`aws_region`**: This field specifies the AWS region where the application is deployed. Make sure to use a region where Amazon Bedrock models are enabled.

5. **`prefix`**: This field allows you to set a prefix for resource names created by the application. You can leave it empty or provide a custom prefix if desired.

6. **`bedrock_models`**:  This field contains a dictionary of Bedrock models that the chatbot can use. Each model is identified by a *key* (e.g., "Sonnet", "Haiku") and, the *key* is the name used in the Chainlit [Chatprofile](https://docs.chainlit.io/advanced-features/chat-profiles). Each model has the following properties:
   - **`id`**: The ID or ARN of the Amazon Bedrock model. You can find the available model IDs in the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html#model-ids-arns).
   - **`cost`**: An object specifying the pricing details for the model. It has the following properties:
     - **`input_1k_price`**: The cost (in USD) for 1,000 input tokens. You can find the pricing information for different models on the [AWS Bedrock pricing page](https://aws.amazon.com/bedrock/pricing/).
     - **`output_1k_price`**: The cost (in USD) for 1,000 output tokens.
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
  "system_prompt": "The initial prompt or instructions for the model.",
  "max_characters_parameter": "Maximum character limit for user input (set to the string 'None' for no limit).",
  "max_content_size_mb_parameter": "Maximum content size (in MB) for user inputs like images (set to the string 'None' for no limit).",
  "aws_region": "The AWS region where you are deploying the application.",
  "prefix": "Optional prefix for created resources.",
  "bedrock_models": {
    "Sonnet": {
      "id": "The unique identifier or ARN of the Bedrock model.",
      "cost": {
        "input_1k_price": "Cost (in USD) for 1,000 input tokens.",
        "output_1k_price": "Cost (in USD) for 1,000 output tokens."
      },
      "default": "boolen value for the default selected model"
    },
    "Haiku": {
      "id": "The unique identifier or ARN of the Bedrock model.",
      "cost": {
        "input_1k_price": "Cost (in USD) for 1,000 input tokens.",
        "output_1k_price": "Cost (in USD) for 1,000 output tokens."
      }
    },
    "any other model name you are adding, used in chainlit chat profile": {
      "id": "The unique identifier or ARN of the Bedrock model.",
      "cost": {
        "input_1k_price": "Cost (in USD) for 1,000 input tokens.",
        "output_1k_price": "Cost (in USD) for 1,000 output tokens."
      }
    }
  }
}
```

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

## Deployment

1. Enable Amazon Bedrock models access in the deployment region:
   [How to enable Amazon Bedrock model access.](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

   Enable at least one of: 
   - Claude 3 Opus
   - Claude 3 Sonnet
   - Claude 3 Haiku

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
4. Select the desired chat profile (e.g., Sonnet, Haiku) to interact with the corresponding Claude model;
5. Type your message or upload an image in the chat input area;
6. Adjust settings like system prompt, temperature, max tokens, and cost display as needed;
7. View the multimodal responses from Claude, including text and images;
8. Use this sample as a fast starting point for building demo/project based on Generative AI on a chatbot console.

Here's a suggested final section for the README about clean up:

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

## Production Deployment Considerations

While the current architecture provides a good starting point for deploying the Foundational LLM Chat application, there are additional considerations for a production-ready deployment:

### Secure Communication with HTTPS

In the current architecture, communication between the CloudFront distribution and the Application Load Balancer (ALB) is over HTTP. For a production deployment, it is strongly recommended to use HTTPS (TLS/SSL) for secure communication:

1. **ALB TLS Termination**: Implement TLS termination on the ALB to secure the communication between CloudFront and the ALB. Note that the ALB already has a security group configured to allow incoming traffic only from the AWS CloudFront distribution's prefix list for HTTP traffic.
2. **ECS Task TLS Termination**: Implement TLS termination on the ECS tasks to secure the communication between the ALB and the ECS tasks.

Enabling HTTPS with TLS termination at both levels (ALB and ECS tasks) ensures end-to-end encryption and enhances the security of the application.

### General Disclaimer

This AWS Sample is intended for demonstration and educational purposes only. It is not designed for production use without further modifications and hardening. Before deploying this application to a production environment, it is crucial to conduct thorough testing, security assessments, and optimizations based on your specific requirements and best practices.

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