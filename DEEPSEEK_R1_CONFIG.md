# DeepSeek R1 Configuration Summary

## Problem

DeepSeek R1 has reasoning **always enabled at the model level**. The model:

- Always returns `reasoningContent` in a separate content block (Block 0)
- Always returns the final answer in a `text` block (Block 1)
- Does NOT accept `thinking` or `reasoning_config` parameters in `additionalModelRequestFields`
- Sending reasoning parameters causes validation errors

## Solution

Added a new flag `no_reasoning_params` to the reasoning configuration object.

## Configuration for DeepSeek R1

```json
"DeepSeek R1": {
  "id": "us.deepseek.r1-v1:0",
  "inference_profile": {
    "prefix": "us",
    "region": "us-west-2"
  },
  "region": ["us-east-1", "us-east-2", "us-west-2"],
  "cost": {
    "input_1k_price": 0.00135,
    "output_1k_price": 0.0054
  },
  "maxTokens": 163840,
  "vision": false,
  "document": true,
  "tool": false,
  "streaming": true,
  "reasoning": {
    "enabled": true,
    "openai_reasoning_modalities": true,
    "no_reasoning_params": true
  }
}
```

## What Each Flag Does

- **`enabled: true`**: Tells the app that reasoning is supported
- **`openai_reasoning_modalities: true`**:
  - Look for `reasoningContent` field in the response (not `thinking`)
  - Show reasoning as always-on in the UI (no toggle)
  - Handle two-block response structure
- **`no_reasoning_params: true`**:
  - **NEW FLAG** - Prevents sending ANY reasoning parameters to the API
  - No `additionalModelRequestFields` for reasoning
  - Avoids validation errors from the model

## Code Changes

### 1. TypeScript Interface (bin/config.ts)

Added `no_reasoning_params?: boolean` to `ReasoningConfig` interface with documentation.

### 2. Python App Logic (chainlit_image/foundational-llm-chat_app/app.py)

Added check before sending reasoning parameters:

```python
if isinstance(reasoning_config, dict) and reasoning_config.get("no_reasoning_params"):
    logger.debug("Model has reasoning always enabled - not sending any reasoning parameters")
    # Don't add any reasoning parameters to additional_model_fields
elif isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities"):
    # ... existing OpenAI logic
else:
    # ... existing Anthropic logic
```

### 3. Documentation (README.md)

- Added `no_reasoning_params` to the configuration parameter list
- Added new example section "Model-Level Reasoning (Always On)"
- Explained when and why to use this flag

## Testing

Verified that DeepSeek R1:

- ✅ Works without any `additionalModelRequestFields`
- ✅ Returns `reasoningContent` in Block 0
- ✅ Returns final answer in Block 1
- ❌ Fails when sending `thinking` parameter
- ✅ Works with the new configuration

## Impact

- **No breaking changes** to existing models
- Only affects models with `no_reasoning_params: true`
- All other reasoning configurations work exactly as before
