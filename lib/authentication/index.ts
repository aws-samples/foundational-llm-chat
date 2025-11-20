// NodeJS Built-Ins:
import * as crypto from "crypto";
import {
  CfnOutput,
  Duration,
  Names,
  RemovalPolicy,
  Stack,
  Token,
} from "aws-cdk-lib";

// External Dependencies:
import { Construct } from "constructs";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as ssm from "aws-cdk-lib/aws-ssm";

export interface CognitoProps {
  readonly cloudFrontDistribution: cloudfront.Distribution;
  readonly prefix: string; // Prefix from the configuration
  readonly cognito_domain: string | undefined;
}

export class Cognito extends Construct {
  public readonly userPool: cognito.UserPool;
  public readonly client: cognito.UserPoolClient;
  public readonly cognitoDomainParameter: ssm.StringParameter;
  public readonly clientIdParameter: ssm.StringParameter;
  public readonly oauth_cognito_client_secret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props: CognitoProps) {
    super(scope, id);

    // Create a new Cognito User Pool
    this.userPool = new cognito.UserPool(
      this,
      "foundational-llm-chat_user_pool",
      {
        userPoolName: `${props.prefix}foundational-llm-chat-user-pool`,
        signInCaseSensitive: false, // Sign-in is not case-sensitive
        signInAliases: {
          email: true, // Allow sign-in with email
        },
        accountRecovery: cognito.AccountRecovery.NONE, // No account recovery mechanism
        mfa: cognito.Mfa.REQUIRED, // Multi-Factor Authentication (MFA) is required
        mfaSecondFactor: {
          sms: false, // SMS-based MFA is not allowed
          otp: true, // One-Time Password (OTP) MFA is allowed
        },
        featurePlan: cognito.FeaturePlan.PLUS,
        standardThreatProtectionMode:
          cognito.StandardThreatProtectionMode.FULL_FUNCTION, // https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security.html
        //  adds security feature but costs more than plain cognito.
        passwordPolicy: {
          minLength: 8, // Minimum length of password is 8 characters
          requireDigits: true, // Require at least one digit in password
          requireLowercase: true, // Require at least one lowercase letter in password
          requireSymbols: true, // Require at least one symbol in password
          requireUppercase: true, // Require at least one uppercase letter in password
          tempPasswordValidity: Duration.days(3),
        },
        removalPolicy: RemovalPolicy.DESTROY, // Destroy when the stack is deleted
      },
    );

    // Create a new Cognito User Pool Client for the application
    this.client = this.userPool.addClient("FoundationalLlmChatApp", {
      oAuth: {
        flows: {
          authorizationCodeGrant: true, // Enable Authorization Code Grant flow
        },
        scopes: [
          cognito.OAuthScope.OPENID, // Include OpenID scope
          cognito.OAuthScope.EMAIL, // Include email scope
          cognito.OAuthScope.PHONE, // Include phone number scope
          cognito.OAuthScope.PROFILE, // Include profile scope
        ],
        callbackUrls: [
          `https://${props.cloudFrontDistribution.distributionDomainName}/auth/oauth/aws-cognito/callback`,
        ], // Callback URL for OAuth flow
      },
      generateSecret: true, // Generate a client secret
      userPoolClientName: `${props.prefix}FoundationalLlmChatApp`, // Client name
      preventUserExistenceErrors: true, // Prevent user existence errors
    });

    // Store the client secret
    this.oauth_cognito_client_secret = new secretsmanager.Secret(
      this,
      "CognitoSecret",
      {
        secretName: `${props.prefix}oauth_cognito_client_secret`,
        description: "to store env variable of ECS as secrets",
        secretStringValue: this.client.userPoolClientSecret,
      },
    );

    let cognitoDomainUrl: string;
    if (props.cognito_domain === undefined || props.cognito_domain === "") {
      // Create a Cognito User Pool Domain
      const cognitoDomain = this.userPool.addDomain("CognitoDomain", {
        cognitoDomain: {
          domainPrefix: this.generateUniqueDomainName({
            // Max length of a Cognito domain prefix is 63 per:
            // https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolDomain.html#CognitoUserPools-CreateUserPoolDomain-request-Domain
            // However, in practice we see validation errors whenever the *overall domain* exceeds
            // this limit - meaning we only have 24-27 (depending on the region name) characters to
            // play with.
            maxLength: 24 - props.prefix.length,
            prefix: props.prefix,
          }),
        },
      });
      cognitoDomainUrl = cognitoDomain.baseUrl().replace("https://", "");
    } else {
      cognitoDomainUrl = props.cognito_domain;
    }

    this.cognitoDomainParameter = new ssm.StringParameter(
      this,
      "CognitoDomainName",
      {
        description: "Cognito domain name",
        parameterName: `${props.prefix.toLowerCase()}CognitoDomainName`,
        stringValue: cognitoDomainUrl, // Use the Cognito domain from Cognito (without https://),
        tier: ssm.ParameterTier.STANDARD,
      },
    );

    this.clientIdParameter = new ssm.StringParameter(this, "cognitoClientid", {
      description: "Cognito client id",
      parameterName: `${props.prefix.toLowerCase()}cognitoClientid`,
      stringValue: this.client.userPoolClientId,
      tier: ssm.ParameterTier.STANDARD,
    });

    // Output the User Pool ID as a CloudFormation output
    new CfnOutput(this, "UserPoolId", {
      value: this.userPool.userPoolId,
      description: "User Pool ID",
    });
  }

  /**
   * Generate a globally-unique but repeatable domain prefix dependent on deployment context
   *
   * This method uses logic inspired by CDK's generatePhysicalName, which is a private method so we
   * can't use that API directly. We also tweak it a little to support passing a user-specified
   * prefix, and allocating remaining character budget depending how long that prefix is.
   *
   * @see https://github.com/aws/aws-cdk/blob/main/packages/aws-cdk-lib/core/lib/private/physical-name-generator.ts
   */
  private generateUniqueDomainName(config: {
    maxLength: number;
    prefix?: string;
  }): string {
    const prefix = config.prefix || "";
    let nFreeChars = config.maxLength - prefix.length;
    if (nFreeChars < 0) {
      throw new Error(
        `Prefix '${prefix}' is longer than the maximum length ${config.maxLength}`,
      );
    }

    const stack = Stack.of(this);
    const nodeUniqueId = Names.nodeUniqueId(this.node);

    const region: string = stack.region;
    if (Token.isUnresolved(region) || !region) {
      throw new Error(
        `Cannot generate a unique ID for ${this.node.path}, because the region is un-resolved or missing`,
      );
    }

    const account: string = stack.account;
    if (Token.isUnresolved(account) || !account) {
      throw new Error(
        `Cannot generate a unique ID for ${this.node.path}, because the account is un-resolved or missing`,
      );
    }

    const unknownStackName = Token.isUnresolved(stack.stackName);
    const sha256 = crypto
      .createHash("sha256")
      .update(prefix)
      .update(nodeUniqueId)
      .update(region)
      .update(account);

    if (!unknownStackName) sha256.update(stack.stackName);

    let maxHashLen: number;
    if (nFreeChars <= 8) {
      maxHashLen = nFreeChars;
    } else {
      maxHashLen = Math.floor(6 + (nFreeChars - 6) / 3);
    }
    const hashPart = sha256.digest("hex").slice(0, maxHashLen);
    nFreeChars -= hashPart.length;

    let maxIdPartLen: number;
    if (nFreeChars <= 4 || unknownStackName) {
      maxIdPartLen = nFreeChars;
    } else {
      maxIdPartLen = Math.floor(2 + (nFreeChars - 2) / 2);
    }
    // Need the condition because .slice(-0) returns whole string:
    const idPart = maxIdPartLen ? nodeUniqueId.slice(-maxIdPartLen) : "";
    nFreeChars -= idPart.length;

    const stackPart = unknownStackName
      ? ""
      : stack.stackName.slice(0, nFreeChars);
    const ret = [prefix, stackPart, idPart, hashPart].join("");
    return ret.toLowerCase();
  }
}
