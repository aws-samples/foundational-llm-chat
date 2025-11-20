"""
Main application for Foundational LLM Chat.
"""

import chainlit as cl
from typing import Dict, List, Any, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from chainlit.input_widget import Switch, Slider, TextInput, Select
import sys
import os
import logging
import json
import re
from mcp import ClientSession

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import system strings
from system_strings import suported_file_string

# Import configuration
from config.app_config import AppConfig

# Import services
from services.thinking_service import ThinkingService
from services.content_service import ContentService

# Import utilities
from utils.message_utils import (
    create_content,
    create_image_content,
    create_doc_content,
    extract_and_process_prompt,
)

# Configure logging
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load configuration
aws_config = AppConfig.load_aws_config()
system_prompt_list = AppConfig.load_system_prompts()
content_limits = AppConfig.load_content_limits()
data_layer_config = AppConfig.load_data_layer_config()
bedrock_models = AppConfig.load_bedrock_models()

# Initialize services
content_service = ContentService(
    max_chars=content_limits["max_chars"],
    max_size_mb=content_limits["max_content_size_mb"],
)

# Define supported file string
suported_file_string = "Supported file types: JPEG, PNG, GIF, WEBP, PDF, CSV, XLSX, XLS, DOCX, DOC, TXT, HTML, MD"


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


# TODO: add data persistence when fixed by chainlit
# import chainlit.data as cl_data
# from chainlit.data.dynamodb import DynamoDBDataLayer
# from chainlit.data.storage_clients import S3StorageClient
# if(data_layer_config["s3_bucket"] and data_layer_config["dynamodb_table"]):
#     storage_client = S3StorageClient(bucket=data_layer_config["s3_bucket"])
#     cl_data._data_layer = DynamoDBDataLayer(
#         table_name=data_layer_config["dynamodb_table"],
#         storage_provider=storage_client
#     )


async def generate_conversation(
    bedrock_client=None,
    model_id=None,
    input_text=None,
    max_tokens=1000,
    images=None,
    docs=None,
):
    """
    Sends messages to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        input_text (str): The text input.
        max_tokens (int): Maximum tokens to generate.
        images (list): List of images to include.
        docs (list): List of documents to include.

    Returns:
        response (JSON): The conversation that the model generated.
    """
    thinking_enabled = cl.user_session.get("thinking_enabled")

    # Get the message history
    message_history = cl.user_session.get("message_history")

    # Check if we have new input or if we're continuing with existing history (e.g., after tool calls)
    if input_text is None and not images and not docs:
        # No new input - we're continuing with existing message history (e.g., after tool calls)
        logger.debug("Continuing with existing message history for tool results")
        api_message_history = message_history.copy()
    else:
        # We have new input - process it normally
        # Create content for the new user message
        images_body = []
        if images:
            logger.debug(f"Creating image content for {len(images)} images")
            images_body = create_image_content(images)
            logger.debug(f"Created image content: {images_body}")

        docs_body = []
        if docs:
            logger.debug(f"Creating document content for {len(docs)} documents")
            docs_body = create_doc_content(docs)
            logger.debug(f"Created document content: {docs_body}")

        # Create the user message content using the create_content function
        new_user_content = create_content(input_text, images_body, docs_body)
        logger.debug(f"Final message content: {new_user_content}")

        # For non-streaming mode with documents, just use the current message
        # This follows AWS example for document handling
        if not cl.user_session.get("streaming") and (docs or images):
            # Create a single message with the document content
            api_message_history = [{"role": "user", "content": new_user_content}]
            logger.debug(
                "Using single message approach for non-streaming document request (AWS recommended pattern)"
            )
        else:
            # For streaming or text-only messages, use the full conversation history
            api_message_history = message_history.copy()
            api_message_history.append({"role": "user", "content": new_user_content})

        # Add the new user message to the session history
        # IMPORTANT: This is the only place where we update the message history
        message_history.append({"role": "user", "content": new_user_content})

    # Log message count only (not full content for cleaner logs)
    logger.debug(f"Sending {len(api_message_history)} messages to model")

    # Base inference parameters to use.
    inference_config = {"maxTokens": max_tokens}

    # Handle temperature based on model type and thinking state
    if not thinking_enabled:
        inference_config["temperature"] = float(cl.user_session.get("temperature"))
        logger.debug(f"Using temperature: {inference_config['temperature']}")
    else:
        # Get current model info to check reasoning type
        chat_profile = cl.user_session.get("chat_profile")
        model_info = bedrock_models[chat_profile] if chat_profile else {}
        reasoning_config = model_info.get("reasoning", {})

        # For OpenAI reasoning models, set temperature and top_p to 1
        if isinstance(reasoning_config, dict) and reasoning_config.get(
            "openai_reasoning_modalities"
        ):
            inference_config["temperature"] = 1.0
            inference_config["topP"] = 1.0
            logger.debug("OpenAI reasoning model: temperature and top_p set to 1.0")
        else:
            logger.debug("Standard thinking model: temperature parameter omitted")

    # Additional inference parameters to use.
    additional_model_fields = {}

    # Add reasoning capability if enabled
    if thinking_enabled:
        # Get current model info to check reasoning type
        chat_profile = cl.user_session.get("chat_profile")
        model_info = bedrock_models[chat_profile] if chat_profile else {}
        reasoning_config = model_info.get("reasoning", {})

        # Check if model has reasoning always enabled at model level (no API params needed)
        if isinstance(reasoning_config, dict) and reasoning_config.get(
            "no_reasoning_params"
        ):
            logger.debug(
                "Model has reasoning always enabled - not sending any reasoning parameters"
            )
            # Don't add any reasoning parameters to additional_model_fields
        # Check if this is an OpenAI reasoning model
        elif isinstance(reasoning_config, dict) and reasoning_config.get(
            "openai_reasoning_modalities"
        ):
            # Use OpenAI reasoning config format
            reasoning_effort = cl.user_session.get("reasoning_effort", "medium")
            additional_model_fields["reasoning_config"] = reasoning_effort
            logger.debug(f"OpenAI reasoning enabled with effort: {reasoning_effort}")
        else:
            # Use standard thinking format for other models
            reasoning_budget = int(cl.user_session.get("reasoning_budget"))
            additional_model_fields["thinking"] = {
                "type": "enabled",
                "budget_tokens": reasoning_budget,
            }
            logger.debug(
                f"Standard thinking enabled with budget: {reasoning_budget} tokens"
            )

            # Check if interleaved thinking is enabled for Claude models
            interleaved_thinking = cl.user_session.get("interleaved_thinking", False)
            if interleaved_thinking and "claude" in model_id.lower():
                # Get available MCP tools to check if we have tools
                mcp_tools = cl.user_session.get("mcp_tools", {})
                has_tools = any(
                    len(conn_data["tools"]) > 0 for conn_data in mcp_tools.values()
                )

                if has_tools:
                    additional_model_fields["anthropic_beta"] = [
                        "interleaved-thinking-2025-05-14"
                    ]
                    logger.debug("Interleaved thinking enabled for Claude with tools")
                else:
                    logger.debug(
                        "Interleaved thinking requested but no tools available"
                    )
    else:
        logger.debug("Thinking disabled")

    # Get available MCP tools and format them for Bedrock
    mcp_tools = cl.user_session.get("mcp_tools", {})
    all_tools = []
    for connection_name, connection_data in mcp_tools.items():
        all_tools.extend(connection_data["tools"])

    # Prepare tool config for Bedrock
    tool_config = None
    if all_tools:
        tool_config = {"tools": all_tools}
        logger.debug(f"Using {len(all_tools)} MCP tools")

    chat_profile = cl.user_session.get("chat_profile")
    logger.debug(f"Calling {chat_profile} with {len(api_message_history)} messages")

    # Prepare API call parameters
    api_params = {
        "modelId": model_id,
        "messages": api_message_history,
        "inferenceConfig": inference_config,
        "additionalModelRequestFields": additional_model_fields,
    }

    # Only add system prompt if it's not empty
    system_prompt = cl.user_session.get("system_prompt")
    if system_prompt and system_prompt[0].get("text", "").strip():
        api_params["system"] = system_prompt

    # Only add toolConfig if it's not None
    if tool_config is not None:
        api_params["toolConfig"] = tool_config

    if cl.user_session.get("streaming"):
        try:
            return bedrock_client.converse_stream(**api_params)
        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A client error occurred: %s", message)
            print("A client error occured: " + format(message))
    else:
        try:
            return bedrock_client.converse(**api_params)
        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A client error occurred: %s", message)
            print("A client error occured: " + format(message))


@cl.set_chat_profiles
async def chat_profile():
    profiles = []
    for key in bedrock_models.keys():
        is_default = None
        if "default" in bedrock_models[key]:
            is_default = bedrock_models[key]["default"]
        profiles.append(
            cl.ChatProfile(
                name=key,
                markdown_description=f"The underlying LLM model is *{key}*.",
                icon=f"public/{bedrock_models[key].get('id').lower()}.png",
                default=is_default if is_default else False,
            )
        )
    return profiles


@cl.on_settings_update
async def set_settings(settings):
    # Get current model info to check streaming capability
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile] if chat_profile else {}
    streaming_supported = model_info.get(
        "streaming", True
    )  # Default to True for backward compatibility

    # Store basic settings
    # Handle streaming - only set if the control exists (streaming supported)
    if "streaming" in settings:
        cl.user_session.set("streaming", settings["streaming"])
    else:
        # If streaming control doesn't exist, force to False
        cl.user_session.set("streaming", False)

    cl.user_session.set("max_tokens", settings["max_tokens"])
    cl.user_session.set("costs", settings["costs"])
    cl.user_session.set("precision", settings["precision"])
    cl.user_session.set("system_prompt", [{"text": settings["system_prompt"]}])

    # Handle thinking settings - check if this is an OpenAI reasoning model
    reasoning_config = model_info.get("reasoning", {})
    is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get(
        "openai_reasoning_modalities"
    )

    if is_openai_reasoning:
        # For OpenAI reasoning models, thinking is always enabled
        thinking_enabled = True
        cl.user_session.set("thinking_enabled", True)
    else:
        # For other models, use the setting value
        thinking_enabled = settings.get("thinking_enabled", False)
        cl.user_session.set("thinking_enabled", thinking_enabled)

    # Handle reasoning effort for OpenAI models
    if "reasoning_effort" in settings:
        cl.user_session.set("reasoning_effort", settings["reasoning_effort"])

    # Handle reasoning budget for standard models
    if "reasoning_budget" in settings:
        cl.user_session.set("reasoning_budget", settings["reasoning_budget"])

    # Handle interleaved thinking for Claude models
    if "interleaved_thinking" in settings:
        cl.user_session.set("interleaved_thinking", settings["interleaved_thinking"])

    # Always set a default temperature, even if the control is hidden
    cl.user_session.set("temperature", settings.get("temperature", 1.0))

    # If thinking is enabled, update UI dynamically
    if thinking_enabled:
        # Build dynamic settings controls
        dynamic_controls = []

        # Add streaming control only if supported
        if streaming_supported:
            dynamic_controls.append(
                Switch(
                    id="streaming",
                    label="Streaming",
                    initial=cl.user_session.get("streaming"),
                )
            )

        # Add common controls
        dynamic_controls.append(
            TextInput(
                id="system_prompt",
                label="System Prompt",
                initial=settings["system_prompt"],
            )
        )

        # Check if this is an OpenAI reasoning model
        reasoning_config = model_info.get("reasoning", {})
        is_openai_reasoning = isinstance(
            reasoning_config, dict
        ) and reasoning_config.get("openai_reasoning_modalities")

        if is_openai_reasoning:
            # For OpenAI models, don't show thinking toggle (always enabled)
            # Add OpenAI reasoning effort control
            dynamic_controls.append(
                Select(
                    id="reasoning_effort",
                    label="Reasoning Effort",
                    values=["low", "medium", "high"],
                    initial_index=["low", "medium", "high"].index(
                        settings.get("reasoning_effort", "medium")
                    ),
                )
            )

        else:
            # For standard models, show thinking toggle and reasoning budget
            dynamic_controls.append(
                Switch(
                    id="thinking_enabled", label="Enable Thinking Process", initial=True
                )
            )
            dynamic_controls.append(
                Slider(
                    id="reasoning_budget",
                    label="Reasoning Budget (tokens)",
                    initial=settings.get("reasoning_budget", 4096),
                    min=1024,
                    max=64000,
                    step=1024,
                )
            )

            # Add interleaved thinking toggle for Claude models (beta feature)
            if "claude" in model_info["id"].lower():
                dynamic_controls.append(
                    Switch(
                        id="interleaved_thinking",
                        label="Interleaved Thinking (Beta) - Think between tool calls",
                        initial=settings.get("interleaved_thinking", False),
                    )
                )

        # Add remaining controls
        dynamic_controls.extend(
            [
                Slider(
                    id="temperature",
                    label="Temperature (disabled when thinking is enabled)",
                    initial=1.0,
                    min=0,
                    max=1,
                    step=0.1,
                    disabled=True,
                ),
                Slider(
                    id="max_tokens",
                    label="Maximum tokens",
                    initial=settings["max_tokens"],
                    min=1,
                    max=model_info.get("maxTokens", 4096),
                    step=1024,
                ),
                Switch(
                    id="costs",
                    label="Show costs in the answer",
                    initial=settings["costs"],
                ),
                Slider(
                    id="precision",
                    label="Digit Precision of costs",
                    initial=settings["precision"],
                    min=1,
                    max=10,
                    step=1,
                ),
            ]
        )

        await cl.ChatSettings(dynamic_controls).send()


@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession):
    """Called when an MCP connection is established"""
    logger.debug(f"MCP Connection established: {connection.name}")

    try:
        # Discover available tools from the MCP server
        result = await session.list_tools()
        tools = []

        for tool in result.tools:
            # Convert MCP tool schema to Bedrock tool format
            bedrock_tool = {
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {"json": tool.inputSchema},
                }
            }
            tools.append(bedrock_tool)
            logger.debug(f"Discovered tool: {tool.name}")

        # Store tools in user session
        mcp_tools = cl.user_session.get("mcp_tools", {})
        mcp_tools[connection.name] = {"tools": tools, "session": session}
        cl.user_session.set("mcp_tools", mcp_tools)

        logger.debug(
            f"Successfully registered {len(tools)} tools from {connection.name}"
        )

    except Exception as e:
        logger.error(f"Error connecting to MCP server {connection.name}: {e}")


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """Called when an MCP connection is terminated"""
    logger.debug(f"MCP Connection terminated: {name}")

    # Remove tools from user session
    mcp_tools = cl.user_session.get("mcp_tools", {})
    if name in mcp_tools:
        tool_count = len(mcp_tools[name]["tools"])
        del mcp_tools[name]
        cl.user_session.set("mcp_tools", mcp_tools)

        logger.debug(f"MCP connection terminated: {name}, removed {tool_count} tools")


@cl.step(type="tool")
async def call_mcp_tool(tool_use_id: str, tool_name: str, tool_input: dict):
    """Execute an MCP tool and return the result"""
    current_step = cl.context.current_step
    current_step.name = tool_name

    logger.debug(f"Calling MCP tool: {tool_name}")

    try:
        # Find which MCP connection has this tool
        mcp_tools = cl.user_session.get("mcp_tools", {})
        mcp_session = None
        connection_name = None

        for conn_name, conn_data in mcp_tools.items():
            for tool in conn_data["tools"]:
                if tool["toolSpec"]["name"] == tool_name:
                    mcp_session = conn_data["session"]
                    connection_name = conn_name
                    break
            if mcp_session:
                break

        if not mcp_session:
            error_msg = f"Tool {tool_name} not found in any MCP connection"
            logger.error(error_msg)
            current_step.output = json.dumps({"error": error_msg})
            return current_step.output

        # Call the MCP tool
        logger.debug(f"Executing {tool_name} via {connection_name}")
        result = await mcp_session.call_tool(tool_name, tool_input)

        # Format the result
        if hasattr(result, "content") and result.content:
            # Handle different content types
            content_parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    content_parts.append(content.text)
                elif hasattr(content, "data"):
                    content_parts.append(str(content.data))
                else:
                    content_parts.append(str(content))

            result_text = "\n".join(content_parts)
            current_step.output = result_text
            logger.debug(f"Tool {tool_name} executed successfully")
        else:
            current_step.output = str(result)

        return current_step.output

    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {str(e)}"
        logger.error(error_msg)
        current_step.output = json.dumps({"error": error_msg})
        return current_step.output


@cl.on_chat_start
async def start():
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile]
    cl.user_session.set("total_cost", 0)
    cl.user_session.set("message_history", [])
    cl.user_session.set("message_contents", [])
    cl.user_session.set("directory_paths", set([]))

    # Store bedrock models for later use
    cl.user_session.set("bedrock_models", bedrock_models)

    try:
        bedrock_client_config = Config(**aws_config)
        if "region" in model_info:
            if len(model_info["region"]) > 1:
                bedrock_client_config.region_name = model_info["inference_profile"][
                    "region"
                ]
            else:
                bedrock_client_config.region_name = model_info["region"]
        cl.user_session.set(
            "bedrock_runtime",
            boto3.client("bedrock-runtime", config=bedrock_client_config),
        )
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occured: " + format(message))
    # Initialize system prompt
    # Initialize system prompt - start with model-specific or empty
    system_prompt = model_info.get("system_prompt", "")

    # Try to get system prompt from Bedrock Prompt Manager if available
    if chat_profile in system_prompt_list:
        try:
            bedrock_agent_client_config = Config(**aws_config)
            bedrock_agent_client = boto3.client(
                "bedrock-agent", config=bedrock_agent_client_config
            )

            system_prompt_object = bedrock_agent_client.get_prompt(
                promptIdentifier=system_prompt_list[chat_profile].get("id"),
                promptVersion=system_prompt_list[chat_profile].get("version"),
            )

            # Use the extract_and_process_prompt function to handle the prompt structure
            prompt_from_manager = extract_and_process_prompt(system_prompt_object)
            if prompt_from_manager:
                system_prompt = prompt_from_manager
                logger.debug(
                    f"Loaded system prompt from Prompt Manager for {chat_profile}: {system_prompt[:50]}..."
                )
            else:
                logger.warning(
                    f"Failed to extract system prompt from Prompt Manager for {chat_profile}"
                )
        except Exception as e:
            logger.error(f"Error getting system prompt from Prompt Manager: {e}")

    # If still no prompt, log it
    if not system_prompt or not system_prompt.strip():
        logger.debug(f"No system prompt available for {chat_profile}")

    cl.user_session.set("system_prompt", [{"text": system_prompt}])

    # Check if the model supports reasoning and streaming
    reasoning_supported = model_info.get("reasoning", False)
    streaming_supported = model_info.get(
        "streaming", True
    )  # Default to True for backward compatibility

    # Build settings controls based on model capabilities
    settings_controls = []

    # Add streaming control based on model capability
    if streaming_supported:
        settings_controls.append(
            Switch(id="streaming", label="Streaming", initial=True)
        )
    # If streaming is not supported, don't add the control at all (it will disappear)

    # Only add reasoning controls if the model supports it
    if reasoning_supported:
        # Check if this is an OpenAI reasoning model
        reasoning_config = model_info.get("reasoning", {})
        is_openai_reasoning = isinstance(
            reasoning_config, dict
        ) and reasoning_config.get("openai_reasoning_modalities")

        if is_openai_reasoning:
            # For OpenAI reasoning models, thinking is always enabled and cannot be toggled
            thinking_enabled = True
            cl.user_session.set("thinking_enabled", thinking_enabled)

            # Don't add the thinking toggle - it's always on for OpenAI models
            # Add OpenAI reasoning effort control
            settings_controls.append(
                Select(
                    id="reasoning_effort",
                    label="Reasoning Effort",
                    values=["low", "medium", "high"],
                    initial_index=1,  # Default to "medium"
                )
            )
            # Set default reasoning effort
            cl.user_session.set("reasoning_effort", "medium")

        else:
            # For standard reasoning models, thinking can be toggled
            thinking_enabled = True
            cl.user_session.set("thinking_enabled", thinking_enabled)

            settings_controls.append(
                Switch(
                    id="thinking_enabled",
                    label="Enable Thinking Process",
                    initial=thinking_enabled,
                )
            )

            # Add standard reasoning budget for non-OpenAI models
            settings_controls.append(
                Slider(
                    id="reasoning_budget",
                    label="Reasoning Budget (tokens)",
                    initial=4096,
                    min=1024,
                    max=64000,
                    step=64,
                )
            )

            # Add interleaved thinking toggle for Claude models (beta feature)
            # Check if this is a Claude model
            if "claude" in model_info["id"].lower():
                settings_controls.append(
                    Switch(
                        id="interleaved_thinking",
                        label="Interleaved Thinking (Beta) - Think between tool calls",
                        initial=False,
                    )
                )
                # Set default value
                cl.user_session.set("interleaved_thinking", False)

        # Add temperature control (disabled when thinking is enabled)
        settings_controls.append(
            Slider(
                id="temperature",
                label="Temperature (disabled when thinking is enabled)",
                initial=1.0,
                min=0,
                max=1,
                step=0.1,
                disabled=thinking_enabled,
            )
        )
    else:
        # Set default values for reasoning settings even if not shown
        cl.user_session.set("thinking_enabled", False)
        cl.user_session.set("reasoning_budget", 4096)

        # Always show temperature for models without reasoning
        settings_controls.append(
            Slider(
                id="temperature",
                label="Temperature",
                initial=1,
                min=0,
                max=1,
                step=0.1,
            )
        )

    # Add remaining controls
    # Use model-specific maxTokens from config if available, otherwise default to 4096
    max_tokens_initial = model_info.get("maxTokens", 4096)
    # Set initial value to 50% of maxTokens but cap at 8192
    initial_tokens = min(max_tokens_initial // 2, 8192)
    settings_controls.extend(
        [
            Slider(
                id="max_tokens",
                label="Maximum tokens",
                initial=initial_tokens,
                min=1,
                max=max_tokens_initial,
                step=64,
            ),
            TextInput(
                id="system_prompt",
                label="System Prompt",
                initial=cl.user_session.get("system_prompt")[0]["text"],
            ),
            Switch(id="costs", label="Show costs in the answer", initial=False),
            Slider(
                id="precision",
                label="Digit Precision of costs",
                initial=4,
                min=1,
                max=10,
                step=1,
            ),
        ]
    )

    settings = await cl.ChatSettings(settings_controls).send()
    await set_settings(settings)


async def process_model_response(response, msg, model_info):
    """Process model response, handling both streaming and tool calls"""
    api_usage = None

    # Check if streaming is enabled
    if cl.user_session.get("streaming"):
        # Handle streaming response
        api_usage = await handle_streaming_response(response, msg, model_info)
    else:
        # Handle non-streaming response
        api_usage = await handle_non_streaming_response(response, msg, model_info)

    # Handle costs display
    if api_usage:
        await display_costs(api_usage, model_info)

    await msg.update()
    return response


async def handle_streaming_response(response, msg, model_info):
    """Handle streaming response with tool call support"""
    stream = response.get("stream")
    if not stream:
        return None

    # For tracking thinking content
    thinking_enabled = cl.user_session.get("thinking_enabled")
    thinking_manager = ThinkingService() if thinking_enabled else None
    thinking_step = None
    api_usage = None

    # Track tool calls during streaming
    tool_calls = []
    current_tool_call = None

    for event in stream:
        if "messageStart" in event:
            logger.debug(f"Message started with role: {event['messageStart']['role']}")

        elif "contentBlockStart" in event:
            # Check if this is a tool use block
            if "toolUse" in event["contentBlockStart"]["start"]:
                tool_use = event["contentBlockStart"]["start"]["toolUse"]
                current_tool_call = {
                    "toolUseId": tool_use["toolUseId"],
                    "name": tool_use["name"],
                    "input": "",
                }
                logger.debug(f"Tool call started: {tool_use['name']}")

        elif "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})

            # Handle regular text content
            if "text" in delta:
                text_content = delta["text"]

                # Check if tools are available to determine if we should filter empty text
                mcp_tools = cl.user_session.get("mcp_tools", {})
                has_tools = any(
                    len(conn_data["tools"]) > 0 for conn_data in mcp_tools.values()
                )

                # Skip empty text content when tools are enabled (models may return empty text with tool calls)
                if has_tools and not text_content.strip():
                    logger.debug(
                        "Skipping empty text content in streaming (tools enabled)"
                    )
                    continue

                # Clean up excessive whitespace while preserving intentional formatting
                # Only clean up if there are more than 2 consecutive newlines
                if "\n\n\n" in text_content:
                    text_content = re.sub(r"\n{3,}", "\n\n", text_content)
                await msg.stream_token(text_content)

            # Handle tool use input
            elif "toolUse" in delta and current_tool_call:
                current_tool_call["input"] += delta["toolUse"]["input"]

            # Handle reasoning content (thinking) if enabled
            elif thinking_enabled and "reasoningContent" in delta:
                if "text" in delta["reasoningContent"]:
                    thinking_text = delta["reasoningContent"]["text"]
                    thinking_manager.add_thinking(thinking_text)

                    if not thinking_step:
                        thinking_step = cl.Step(
                            name="Thinking 🤔", type="thinking", parent_id=msg.id
                        )
                        await thinking_step.send()
                        logger.debug(
                            f"Created thinking step (streaming) with parent_id: {msg.id}"
                        )

                    await thinking_step.stream_token(thinking_text)

                # Handle signature in reasoning content
                if "signature" in delta["reasoningContent"]:
                    signature = delta["reasoningContent"]["signature"]
                    thinking_manager.set_signature(signature)
                    logger.debug(f"Received thinking signature: {signature[:20]}...")

        elif "contentBlockStop" in event:
            # Complete tool call if we were building one
            if current_tool_call:
                try:
                    current_tool_call["input"] = json.loads(current_tool_call["input"])
                    tool_calls.append(current_tool_call)
                    logger.debug(f"Tool call completed: {current_tool_call['name']}")
                except json.JSONDecodeError:
                    logger.error(
                        f"Failed to parse tool input: {current_tool_call['input']}"
                    )
                current_tool_call = None

            # Complete thinking step
            if thinking_step:
                await thinking_step.update()

        elif "messageStop" in event:
            stop_reason = event["messageStop"]["stopReason"]
            logger.debug(f"Message stopped with reason: {stop_reason}")

            # If we have tool calls, execute them
            if tool_calls and stop_reason == "tool_use":
                await execute_tool_calls(tool_calls, msg, model_info, thinking_manager)

        elif "metadata" in event:
            metadata = event["metadata"]
            if "usage" in metadata:
                api_usage = {
                    "inputTokenCount": metadata["usage"]["inputTokens"],
                    "outputTokenCount": metadata["usage"]["outputTokens"],
                    "invocationLatency": "not available in this API call",
                    "firstByteLatency": "not available in this API call",
                }
            if "metrics" in event["metadata"]:
                api_usage["invocationLatency"] = metadata["metrics"]["latencyMs"]

    # Only store message in history if we didn't have tool calls (tool calls handle their own storage)
    if not tool_calls:
        await store_assistant_message(
            msg.content, thinking_manager, tool_calls_made=False
        )

    return api_usage


async def handle_non_streaming_response(response, msg, model_info):
    """Handle non-streaming response with tool call support"""
    thinking_enabled = cl.user_session.get("thinking_enabled")
    thinking_manager = ThinkingService() if thinking_enabled else None

    # Check if response is valid
    if not response or "output" not in response or "message" not in response["output"]:
        error_msg = "Error: Failed to get a valid response from the model."
        logger.error(f"{error_msg} Response: {response}")
        msg.content = error_msg
        return None

    output_message = response["output"]["message"]
    stop_reason = response.get("stopReason", "")

    # Process content and extract text/thinking
    text = ""
    tool_calls = []
    thinking_step = None

    # Check if tools are available to determine if we should filter empty text
    mcp_tools = cl.user_session.get("mcp_tools", {})
    has_tools = any(len(conn_data["tools"]) > 0 for conn_data in mcp_tools.values())

    for content_item in output_message.get("content", []):
        if "text" in content_item:
            text_content = content_item["text"]
            # Skip empty text content when tools are enabled (models may return empty text with tool calls)
            if has_tools and not text_content.strip():
                logger.debug("Skipping empty text content (tools enabled)")
                continue
            text += text_content
        elif "toolUse" in content_item:
            tool_calls.append(content_item["toolUse"])
        elif thinking_enabled and "reasoningContent" in content_item:
            # Handle thinking content
            if "reasoningText" in content_item["reasoningContent"]:
                thinking_text = content_item["reasoningContent"]["reasoningText"][
                    "text"
                ]
                thinking_signature = content_item["reasoningContent"][
                    "reasoningText"
                ].get("signature")

                thinking_manager.add_thinking(thinking_text)
                if thinking_signature:
                    thinking_manager.set_signature(thinking_signature)
                    logger.debug(
                        f"Received thinking signature (non-streaming): {thinking_signature[:20]}..."
                    )

                # Create thinking step only once with proper parent relationship
                if not thinking_step:
                    thinking_step = cl.Step(
                        name="Thinking 🤔", type="thinking", parent_id=msg.id
                    )
                    await thinking_step.send()
                    logger.debug(f"Created thinking step with parent_id: {msg.id}")

                # Stream the thinking content
                await thinking_step.stream_token(thinking_text)

    # Complete the thinking step if it was created
    if thinking_step:
        await thinking_step.update()
        logger.debug("Completed thinking step")

    # Update message content with cleaned text
    # Clean up excessive whitespace while preserving intentional formatting
    if "\n\n\n" in text:
        text = re.sub(r"\n{3,}", "\n\n", text)

    # Handle message content based on what the model provided
    if text.strip():
        # Model provided text response
        msg.content = text
    elif tool_calls:
        # Model only used thinking + tool calls, provide a helpful placeholder
        msg.content = "🔧 *Using tools to help answer your question...*"
        logger.debug("Model only used thinking + tool calls, using placeholder text")
    else:
        # Fallback for any other case
        msg.content = text

    # Handle tool calls if present
    if tool_calls and stop_reason == "tool_use":
        # Make sure the message is updated with placeholder text before tool execution
        await msg.update()
        await execute_tool_calls(tool_calls, msg, model_info, thinking_manager)

    # Only store message in history if we didn't have tool calls (tool calls handle their own storage)
    if not tool_calls:
        await store_assistant_message(text, thinking_manager, tool_calls_made=False)

    # Extract usage information
    api_usage = {
        "inputTokenCount": response["usage"]["inputTokens"],
        "outputTokenCount": response["usage"]["outputTokens"],
        "invocationLatency": response["metrics"]["latencyMs"],
        "firstByteLatency": "not available in this API call",
    }

    return api_usage


async def execute_tool_calls(tool_calls, msg, model_info, thinking_manager=None):
    """Execute tool calls and get follow-up response"""
    message_history = cl.user_session.get("message_history")

    logger.debug(f"Executing {len(tool_calls)} tool calls")

    # Add the assistant's message with tool calls to history
    assistant_content = []

    # If thinking is enabled and we have thinking content, add it first
    thinking_enabled = cl.user_session.get("thinking_enabled")
    if thinking_enabled and thinking_manager and thinking_manager.has_thinking():
        # Check if model supports signatures
        reasoning_config = model_info.get("reasoning", {})
        is_openai_reasoning = isinstance(
            reasoning_config, dict
        ) and reasoning_config.get("openai_reasoning_modalities")
        include_signature = (
            not is_openai_reasoning
        )  # OpenAI models don't support signatures

        # Get thinking blocks formatted for API
        api_blocks = thinking_manager.get_api_blocks(
            include_signature=include_signature
        )
        assistant_content.extend(api_blocks)

    # Add text content if any
    if msg.content:
        assistant_content.append({"text": msg.content})

    # Add tool calls
    for tool_call in tool_calls:
        assistant_content.append({"toolUse": tool_call})

    assistant_message = {"role": "assistant", "content": assistant_content}
    message_history.append(assistant_message)

    # Execute each tool and collect results
    tool_results = []
    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call["name"]
        tool_input = tool_call["input"]
        tool_use_id = tool_call["toolUseId"]

        # Show progress for multiple tools
        if len(tool_calls) > 1:
            logger.debug(f"Executing tool {i}/{len(tool_calls)}: {tool_name}")
        else:
            logger.debug(f"Executing tool: {tool_name}")

        # Execute the tool
        tool_result = await call_mcp_tool(tool_use_id, tool_name, tool_input)

        tool_results.append(
            {
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"text": str(tool_result)}],
                }
            }
        )

    # Add tool results to message history
    tool_result_message = {"role": "user", "content": tool_results}
    message_history.append(tool_result_message)

    # Call the model again with tool results
    logger.debug("Getting model response to tool results")

    try:
        follow_up_response = await generate_conversation(
            cl.user_session.get("bedrock_runtime"),
            model_info["id"],
            None,  # No new input text
            int(cl.user_session.get("max_tokens")),
            None,
            None,  # No new images/docs
        )

        # Check if we got a valid response
        if follow_up_response is None:
            logger.error("Failed to get response from model after tool execution")
            await cl.Message(
                content="❌ **Error**: Failed to get response from model after tool execution"
            ).send()
            return

        # Create a new message for the follow-up response
        follow_up_msg = cl.Message(content="")
        await follow_up_msg.send()

        # Process the follow-up response with the new message
        await process_model_response(follow_up_response, follow_up_msg, model_info)

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        await cl.Message(content=f"❌ **Tool Execution Error**: {str(e)}").send()
        return


async def store_assistant_message(text, thinking_manager, tool_calls_made=False):
    """Store assistant message in history with proper reasoning handling"""
    message_history = cl.user_session.get("message_history")
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile] if chat_profile else {}
    reasoning_config = model_info.get("reasoning", {})
    is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get(
        "openai_reasoning_modalities"
    )

    # Determine if reasoning should be included based on model type and tool calls
    should_include_reasoning = True
    if is_openai_reasoning:
        # For OpenAI models: only include reasoning if tool calls were made
        should_include_reasoning = tool_calls_made
        logger.debug(
            f"OpenAI reasoning model: tool_calls_made={tool_calls_made}, including_reasoning={should_include_reasoning}"
        )
    else:
        # For Anthropic models: always include reasoning
        should_include_reasoning = True
        logger.debug("Anthropic model: always including reasoning")

    thinking_enabled = cl.user_session.get("thinking_enabled")

    if (
        thinking_enabled
        and thinking_manager
        and thinking_manager.has_thinking()
        and should_include_reasoning
    ):
        # Check if model supports signatures (reuse the model_info we already have)
        include_signature = (
            not is_openai_reasoning
        )  # OpenAI models don't support signatures

        # Get thinking blocks formatted for API
        api_blocks = thinking_manager.get_api_blocks(
            include_signature=include_signature
        )

        # Add to message history with properly formatted thinking blocks
        message_history.append(
            {"role": "assistant", "content": [{"text": text}] + api_blocks}
        )

        logger.debug(
            f"Stored assistant message with thinking blocks in message history"
        )
    else:
        # Add to message history without thinking blocks
        message_history.append({"role": "assistant", "content": [{"text": text}]})
        if is_openai_reasoning and not should_include_reasoning:
            logger.debug(
                "OpenAI reasoning model: reasoning content excluded from history (no tool calls)"
            )


async def display_costs(api_usage, model_info):
    """Display cost information if enabled"""
    if not api_usage:
        return

    invocation_cost = (
        api_usage["inputTokenCount"] / 1000 * model_info["cost"]["input_1k_price"]
        + api_usage["outputTokenCount"] / 1000 * model_info["cost"]["output_1k_price"]
    )
    total_cost = cl.user_session.get("total_cost") + invocation_cost
    cl.user_session.set("total_cost", total_cost)

    logger.debug(f"Invocation cost: {invocation_cost:.4f}, Total: {total_cost:.4f}")

    if cl.user_session.get("costs"):
        precision = cl.user_session.get("precision")
        s_invocation_cost = f"{invocation_cost:.{precision}f}".rstrip("0") or "0.00"
        s_total_cost = f"{total_cost:.{precision}f}".rstrip("0") or "0.00"
        elements = [
            cl.Text(
                name="Invocation cost",
                content=f"Invocation cost: {s_invocation_cost}$",
                display="inline",
            ),
            cl.Text(
                name="Chat cost",
                content=f"Total chat cost: {s_total_cost}$",
                display="inline",
            ),
        ]
        await cl.Message(content="", elements=elements).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Entrypoint for handling user messages with MCP tool support.
    """
    msg = cl.Message(content="")
    await msg.send()  # loading
    await msg.update()
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile]
    max_tokens = int(cl.user_session.get("max_tokens"))

    # Process message contents
    images, docs, other_files = content_service.split_message_contents(
        message, model_info["id"]
    )

    # Log processed contents only if there are attachments
    if images or docs or other_files:
        logger.debug(
            f"Processed contents: images={len(images)}, docs={len(docs)}, other_files={len(other_files)}"
        )

    # Store content for later cleanup
    cl.user_session.set("message_contents", images + docs)

    # Handle unsupported files
    if len(other_files) > 0:
        name_string = ", ".join([other["name"] for other in other_files])
        message_info = f"The files {name_string} is not supported by the model you are using: {model_info['id']}. Not considering it"
        elements = [
            cl.Text(name="Warning", content=message_info, display="inline"),
        ]
        await cl.Message(
            content="",
            elements=elements,
        ).send()
        content_service.delete_contents(other_files)

    # Verify content is valid
    if not content_service.verify_content(message.content, images, docs):
        await cl.Message(
            content=f"Please provide a valid document or image or text. {suported_file_string}"
        ).send()
        content_service.delete_contents(images + docs)
        await msg.update()
        return

    # Log what we're sending to the model (only if there are attachments)
    if images or docs:
        logger.debug(
            f"Sending to model: text + {len(images)} images + {len(docs)} docs"
        )

    # Add user message to history
    message_history = cl.user_session.get("message_history")
    # This will be added in generate_conversation

    api_usage = None
    try:
        response = await generate_conversation(
            cl.user_session.get("bedrock_runtime"),
            model_info["id"],
            message.content,
            max_tokens,
            images,
            docs,
        )

        # Handle streaming and non-streaming responses with tool support
        await process_model_response(response, msg, model_info)

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        await cl.Message(content=f"❌ **Error**: {message}").send()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await cl.Message(content=f"❌ **Unexpected Error**: {str(e)}").send()


@cl.on_chat_end
def on_chat_end():
    # sometimes chainlit does not automatically delete the uploaded files.
    # So we are removing all the files to garantee the privacy
    message_contents = cl.user_session.get("message_contents")
    content_service.delete_contents(message_contents, True)
