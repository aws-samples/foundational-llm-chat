# Changelog

## [Unreleased]

Data Persistance using DynamoDB. Waiting for this issue: https://github.com/Chainlit/chainlit/issues/1172

## [1.3.1] - 2025-03-13

### Changed
- Code refactoring for better organization and maintainability
- Improved code structure and documentation
- Enhanced error handling and logging

## [1.3.0] - 2025-03-13

### Added
- Added Claude 3.7
- Added a way to operate with thinking models

### Changed
- Upgraded the codebase to chainlit 2.0
- Upgraded dependencies to latest version

## [1.2.1] - 2024-12-17

### Added
- Added Amazon Nova
- Added resources for data persistence waiting for new 2.0 chainlit version to enable them

### Changed
- bumped chainlit version to last stable

## [1.2.0] - 2024-10-28

### Added
- Support for Amazon Bedrock inference profiles in `config.json`
- Cross-region endpoint configuration for Amazon Bedrock models
- Implementation of Amazon Bedrock Prompt Manager for enhanced prompt handling

### Changed
- Updated Chainlit to version 1.3.1
- Upgraded Docker image to python:3.12-alpine 3.20
- Expanded region support for Amazon Bedrock models in `config.json`

### Improved
- Enhanced configuration flexibility for Amazon Bedrock models
- Better support for cross-region model deployment

## [1.1.0] - 2024-04-17
- Moved to Amazon Bedrock Converse API to support many more models: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html. We aim to support every model which supports system prompt and docuement chat;
- you can now set system prompt and region in the model configuration;

## [1.0.0] - 2024-04-17
- Initial release
