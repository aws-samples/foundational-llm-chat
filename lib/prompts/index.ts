import { CfnOutput, CfnResource } from "aws-cdk-lib";
import { Construct } from "constructs";
import { BedrockModels } from "../../bin/config";

export interface PromptsProps {
  readonly bedrock_models: BedrockModels;
  readonly default_system_prompt: string;
}

export interface Prompt {
  id: string;
  version: string;
  arn: string;
}

export interface ModelPrompts {
  [key: string]: Prompt;
}

export class Prompts extends Construct {
  public readonly promptsIdList: ModelPrompts = {};

  constructor(scope: Construct, id: string, props: PromptsProps) {
    super(scope, id);

    Object.entries(props.bedrock_models).forEach(([modelName, modelConfig], index) => {
      const sanitizedModelName = this.sanitizeModelName(modelName);
      const promptText = modelConfig.system_prompt || props.default_system_prompt;
      const inputVariables = this.extractInputVariables(promptText);

      const prompt = new CfnResource(this, `Prompt-${sanitizedModelName}-${index}`, {
        type: 'AWS::Bedrock::Prompt',
        properties: {
          Name: `${sanitizedModelName}Prompt${index}`,
          Variants: [
            {
              InferenceConfiguration: { "Text": {} },
              Name: `${sanitizedModelName}Variant${index}`,
              TemplateType: "TEXT",
              TemplateConfiguration: {
                Text: {
                  Text: promptText,
                  InputVariables: inputVariables
                }
              }
            }
          ]
        }
      });

      const promptVersion = new CfnResource(this, `PVersion-${sanitizedModelName}-${index}`, {
        type: 'AWS::Bedrock::PromptVersion',
        properties: {
          Description: `Prompt version for ${modelName}`,
          PromptArn: prompt.getAtt('Arn').toString(),
        }
      });

      const arn = promptVersion.getAtt('Arn').toString();
      const promptId = promptVersion.getAtt('PromptId').toString();
      const version = promptVersion.getAtt('Version').toString();

      this.promptsIdList[modelName] = {
        id: promptId,
        version: version,
        arn: arn
      };
    });
  }

  private extractInputVariables(promptText: string): { Name: string }[] {
    const regex = /{{(\w+)}}/g;
    const matches = promptText.match(regex) || [];
    return matches.map(match => ({
      Name: match.replace(/{{|}}/g, '')
    }));
  }

  private sanitizeModelName(modelName: string): string {
    // Remove any characters that are not alphanumeric, underscore, or hyphen
    let sanitized = modelName.replace(/[^a-zA-Z0-9_-]/g, '');
    
    // Ensure it starts with an alphanumeric character
    sanitized = sanitized.replace(/^[^a-zA-Z0-9]+/, '');
    
    // Truncate to 100 characters if longer
    sanitized = sanitized.slice(0, 100);
    
    // If empty after sanitization, use a default name
    if (sanitized.length === 0) {
      sanitized = 'DefaultModelName';
    }
    
    return sanitized;
  }
}
