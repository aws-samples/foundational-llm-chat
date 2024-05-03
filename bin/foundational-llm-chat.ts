#!/usr/bin/env node

// This line ensures that the source map support is registered, which provides
// a better experience when debugging code in production.
import 'source-map-support/register';

// Importing the required AWS CDK libraries and the FoundationalLlmChatStack class.
import * as cdk from 'aws-cdk-lib';
import { FoundationalLlmChatStack } from '../lib/foundational-llm-chat-stack';
import { getConfig } from "./config";

// Creating a new instance of the AWS CDK App, which represents the root of the CDK application.
const app = new cdk.App();

// get configuration
const config = getConfig();

// Creating a new instance of the FoundationalLlmChatStack with the app, stack name, and AWS region.
// The FoundationalLlmChatStack is the main stack that orchestrates the deployment of the Chatbot application.
new FoundationalLlmChatStack(app, `${config.prefix}FoundationalLlmChatStack`, {
  config,
  env: {
    region: process.env.CDK_DEFAULT_REGION,
    account: process.env.CDK_DEFAULT_ACCOUNT,
  },
});
