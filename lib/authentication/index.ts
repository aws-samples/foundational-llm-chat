import { CfnOutput, Duration, RemovalPolicy } from "aws-cdk-lib";
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
          domainPrefix: `${props.prefix.toLowerCase()}foundational-llm-chat${Math.floor(Math.random() * (10000 - 100) + 100)}`, // Domain prefix for the Cognito domain
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
}
