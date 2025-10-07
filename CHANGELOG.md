# Changelog

## [Unreleased]

Data Persistance using DynamoDB. Waiting for this issue: https://github.com/Chainlit/chainlit/issues/1172

## [1.4.0] - 2025-01-10

### Added

- **MCP (Model Context Protocol) Integration**: Full support for tool calling via MCP servers
  - Client-side MCP connections with per-user isolation
  - Automatic tool discovery and registration
  - Support for multiple concurrent MCP connections
  - Tool execution with proper error handling
- **New Reasoning Parameter**: `no_reasoning_params` flag for models with built-in reasoning
  - Prevents sending reasoning parameters to models where reasoning is always enabled (e.g., DeepSeek R1)
  - Properly handles `reasoningContent` responses without API parameter conflicts
- **Enhanced Model Support**:
  - DeepSeek R1 with native reasoning support
  - DeepSeek V3 with OpenAI-style reasoning
  - OpenAI GPT OSS models (20B, 120B)
  - Qwen models (3 32B, 3 235B variants, Coder models)
  - Writer Palmyra X4 and X5
  - Mistral Pixtral Large with vision
  - Meta Llama 3.3 70B and Llama 4 variants (Scout, Maverick)
  - Claude Sonnet 4.5 with global inference profiles
- **Global Inference Profiles**: Support for worldwide model routing
  - Cross-region inference with automatic failover
  - Global inference profiles for maximum availability
  - Configurable inference profiles per model
- **Streaming Control**: Per-model streaming configuration
  - `streaming` parameter to enable/disable streaming for specific models
  - Automatic UI adaptation based on model capabilities

### Changed

- **Reasoning Configuration**: Enhanced reasoning parameter structure
  - Support for three formats: boolean `false`, boolean `true`, or detailed object
  - `openai_reasoning_modalities` for OpenAI-style reasoning (effort levels)
  - `no_reasoning_params` for models with built-in reasoning
  - `hybrid`, `budget_thinking_tokens`, `temperature_forced` for Anthropic models
- **TypeScript Interfaces**: Updated `ReasoningConfig` interface with comprehensive documentation
- **Code Organization**: Refactored reasoning logic for better maintainability
  - Separated handling for standard thinking, OpenAI reasoning, and model-level reasoning
  - Improved error handling and logging

### Improved

- **Documentation**: Comprehensive updates to README
  - Detailed reasoning parameter examples with real-world configurations
  - Cross-region and global inference profile explanations
  - MCP integration documentation
  - New FAQ entry about MCP storage and user isolation
  - Updated model list with latest additions
- **Configuration Examples**: Added multiple reasoning configuration patterns
  - No reasoning support
  - Simple Anthropic-style reasoning
  - Advanced Anthropic-style reasoning
  - OpenAI-style reasoning
  - Model-level reasoning (always on)

### Fixed

- Corrected file path reference in README (`message_utils.py` instead of `massages_utils.py`)
- Proper handling of DeepSeek R1 reasoning without API parameter conflicts

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
