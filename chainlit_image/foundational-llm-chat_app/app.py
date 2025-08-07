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
    create_content, create_image_content, create_doc_content, 
    extract_and_process_prompt
)

# Configure logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Load configuration
aws_config = AppConfig.load_aws_config()
system_prompt_list = AppConfig.load_system_prompts()
content_limits = AppConfig.load_content_limits()
data_layer_config = AppConfig.load_data_layer_config()
bedrock_models = AppConfig.load_bedrock_models()

# Initialize services
content_service = ContentService(
    max_chars=content_limits["max_chars"],
    max_size_mb=content_limits["max_content_size_mb"]
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

async def generate_conversation(bedrock_client=None, model_id=None, input_text=None, max_tokens=1000, images=None, docs=None):
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
    if input_text is None and not images and not docs:
        raise ValueError("input_text, images, or docs must be provided")
    
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
        logger.debug("Using single message approach for non-streaming document request (AWS recommended pattern)")
    else:
        # For streaming or text-only messages, use the full conversation history
        api_message_history = message_history.copy()
        api_message_history.append({"role": "user", "content": new_user_content})
    
    # Add the new user message to the session history
    # IMPORTANT: This is the only place where we update the message history
    message_history.append({"role": "user", "content": new_user_content})
    
    # Log the raw message history being sent to the model
    logger.debug(f"Raw message history being sent to the model: {api_message_history}")

    # Base inference parameters to use.
    inference_config = {
        "maxTokens": max_tokens
    }
    
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
        if isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities"):
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
        
        # Check if this is an OpenAI reasoning model
        if isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities"):
            # Use OpenAI reasoning effort format
            reasoning_effort = cl.user_session.get("reasoning_effort", "medium")
            additional_model_fields["reasoning_effort"] = reasoning_effort
            logger.debug(f"OpenAI reasoning enabled with effort: {reasoning_effort}")
        else:
            # Use standard thinking format for other models
            reasoning_budget = int(cl.user_session.get("reasoning_budget"))
            additional_model_fields["thinking"] = {
                "type": "enabled",
                "budget_tokens": reasoning_budget
            }
            logger.debug(f"Standard thinking enabled with budget: {reasoning_budget} tokens")
    else:
        logger.debug("Thinking disabled")
        
    # Enhanced logging for debugging - show exact JSON fields sent to Converse API
    import json
    chat_profile = cl.user_session.get("chat_profile")
    
    logger.info("=" * 80)
    logger.info(f"🚀 CONVERSE API CALL - MODEL: {chat_profile} ({model_id})")
    logger.info("=" * 80)
    
    # Create the exact payload structure that will be sent to Converse API (excluding system prompt)
    api_payload = {
        "modelId": model_id,
        "messages": api_message_history,
        "inferenceConfig": inference_config if inference_config else None,
        "additionalModelRequestFields": additional_model_fields if additional_model_fields else None
    }
    
    # Note: system prompt is sent but excluded from log due to length
    
    logger.info("📋 EXACT JSON PAYLOAD:")
    logger.info(json.dumps(api_payload, indent=2, default=str))
    logger.info("=" * 80)
    
    if cl.user_session.get("streaming"):
        try: 
            return bedrock_client.converse_stream(
                modelId=model_id,
                messages=api_message_history,
                system=cl.user_session.get("system_prompt"),
                inferenceConfig=inference_config,
                additionalModelRequestFields=additional_model_fields
            )
        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A client error occurred: %s", message)
            print("A client error occured: " +
                format(message))
    else:
        try:
            return bedrock_client.converse(
                modelId=model_id,
                messages=api_message_history,
                system=cl.user_session.get("system_prompt"),
                inferenceConfig=inference_config,
                additionalModelRequestFields=additional_model_fields
            )
        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A client error occurred: %s", message)
            print("A client error occured: " +
                format(message))
    
@cl.set_chat_profiles
async def chat_profile():
    profiles = []
    for key in bedrock_models.keys():
        is_default = None
        if "default" in bedrock_models[key]:
            is_default = bedrock_models[key]["default"]
        profiles.append(cl.ChatProfile(name=key, 
                                       markdown_description=f"The underlying LLM model is *{key}*.", 
                                       icon=f"public/{bedrock_models[key].get('id').lower()}.png",
                                       default = is_default if is_default else False))
    return profiles

@cl.on_settings_update
async def set_settings(settings):
    # Get current model info to check streaming capability
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile] if chat_profile else {}
    streaming_supported = model_info.get("streaming", True)  # Default to True for backward compatibility
    
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
    is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities")
    
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
    
    # Handle send reasoning back toggle for OpenAI models
    if "send_reasoning_back" in settings:
        cl.user_session.set("send_reasoning_back", settings["send_reasoning_back"])
    
    # Handle reasoning budget for standard models
    if "reasoning_budget" in settings:
        cl.user_session.set("reasoning_budget", settings["reasoning_budget"])
    
    # Always set a default temperature, even if the control is hidden
    cl.user_session.set("temperature", settings.get("temperature", 1.0))
    
    # If thinking is enabled, update UI dynamically
    if thinking_enabled:
        # Build dynamic settings controls
        dynamic_controls = []
        
        # Add streaming control only if supported
        if streaming_supported:
            dynamic_controls.append(
                Switch(id="streaming", label="Streaming", initial=cl.user_session.get("streaming"))
            )
        
        # Add common controls
        dynamic_controls.append(
            TextInput(id="system_prompt", label="System Prompt", initial=settings["system_prompt"])
        )
        
        # Check if this is an OpenAI reasoning model
        reasoning_config = model_info.get("reasoning", {})
        is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities")
        
        if is_openai_reasoning:
            # For OpenAI models, don't show thinking toggle (always enabled)
            # Add OpenAI reasoning effort control
            dynamic_controls.append(
                Select(
                    id="reasoning_effort",
                    label="Reasoning Effort",
                    values=["low", "medium", "high"],
                    initial_index=["low", "medium", "high"].index(settings.get("reasoning_effort", "medium"))
                )
            )
            # Add toggle for sending reasoning back in conversation
            dynamic_controls.append(
                Switch(
                    id="send_reasoning_back", 
                    label="Send Reasoning Back in Conversation", 
                    initial=settings.get("send_reasoning_back", False)
                )
            )
        else:
            # For standard models, show thinking toggle and reasoning budget
            dynamic_controls.append(
                Switch(id="thinking_enabled", label="Enable Thinking Process", initial=True)
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
        
        # Add remaining controls
        dynamic_controls.extend([
            Slider(
                id="temperature",
                label="Temperature (disabled when thinking is enabled)",
                initial=1.0,
                min=0,
                max=1,
                step=0.1,
                disabled=True
            ),
            Slider(
                id="max_tokens",
                label="Maximum tokens",
                initial=settings["max_tokens"],
                min=1,
                max=model_info.get("maxTokens", 4096),
                step=1024,
            ),
            Switch(id="costs", label="Show costs in the answer", initial=settings["costs"]),
            Slider(id="precision", label="Digit Precision of costs", initial=settings["precision"], min=1, max=10, step=1)
        ])
        
        await cl.ChatSettings(dynamic_controls).send()

@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession):
    """Called when an MCP connection is established"""
    # Your connection initialization code here
    # This handler is required for MCP to work
    
@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """Called when an MCP connection is terminated"""
    # Your cleanup code here
    # This handler is optional

@cl.on_chat_start
async def start():
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile]
    cl.user_session.set(
        "total_cost",
        0
    )
    cl.user_session.set(
        "message_history",
        []
    )
    cl.user_session.set(
        "message_contents",
        []
    )
    cl.user_session.set(
        "directory_paths",
        set([])
    )
    
    # Store bedrock models for later use
    cl.user_session.set("bedrock_models", bedrock_models)
    
    try:
        bedrock_client_config = Config(**aws_config)
        if "region" in model_info:
            if len(model_info["region"]) > 1:
                bedrock_client_config.region_name = model_info["inference_profile"]["region"]
            else:
                bedrock_client_config.region_name = model_info["region"]
        cl.user_session.set("bedrock_runtime", boto3.client('bedrock-runtime', config=bedrock_client_config))
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occured: " +
              format(message))
    # Initialize system prompt
    system_prompt = ""
    
    # Try to get system prompt if available
    if chat_profile in system_prompt_list:
        try:
            bedrock_agent_client_config = Config(**aws_config)
            bedrock_agent_client = boto3.client('bedrock-agent', config=bedrock_agent_client_config)
            
            system_prompt_object = bedrock_agent_client.get_prompt(
                promptIdentifier=system_prompt_list[chat_profile].get("id"),
                promptVersion=system_prompt_list[chat_profile].get("version")
            )
            
            # Use the extract_and_process_prompt function to handle the prompt structure
            system_prompt = extract_and_process_prompt(system_prompt_object)
            if system_prompt:
                logger.debug(f"Loaded system prompt for {chat_profile}: {system_prompt[:50]}...")
            else:
                logger.warning(f"Failed to extract system prompt for {chat_profile}")
        except Exception as e:
            logger.error(f"Error getting system prompt: {e}")
    else:
        logger.debug(f"No system prompt defined for {chat_profile}")
        
    cl.user_session.set(
        "system_prompt",
        [{"text": system_prompt}]
    )
    
    # Check if the model supports reasoning and streaming
    reasoning_supported = model_info.get("reasoning", False)
    streaming_supported = model_info.get("streaming", True)  # Default to True for backward compatibility
    
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
        is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities")
        
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
                    initial_index=1  # Default to "medium"
                )
            )
            # Set default reasoning effort
            cl.user_session.set("reasoning_effort", "medium")
            
            # Add toggle to control whether reasoning content is sent back in conversation history
            settings_controls.append(
                Switch(
                    id="send_reasoning_back", 
                    label="Send Reasoning Back in Conversation", 
                    initial=False  # Default to False for safer behavior
                )
            )
            # Set default value
            cl.user_session.set("send_reasoning_back", False)
        else:
            # For standard reasoning models, thinking can be toggled
            thinking_enabled = True
            cl.user_session.set("thinking_enabled", thinking_enabled)
            
            settings_controls.append(
                Switch(id="thinking_enabled", label="Enable Thinking Process", initial=thinking_enabled)
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
        
        # Add temperature control (disabled when thinking is enabled)
        settings_controls.append(
            Slider(
                id="temperature",
                label="Temperature (disabled when thinking is enabled)",
                initial=1.0,
                min=0,
                max=1,
                step=0.1,
                disabled=thinking_enabled
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
    settings_controls.extend([
        Slider(
            id="max_tokens",
            label="Maximum tokens",
            initial=initial_tokens,
            min=1,
            max=max_tokens_initial,
            step=64,
        ),
        TextInput(id="system_prompt", label="System Prompt", initial=cl.user_session.get("system_prompt")[0]["text"]),
        Switch(id="costs", label="Show costs in the answer", initial=False),
        Slider(id="precision", label="Digit Precision of costs", initial=4, min=1, max=10, step=1)
    ])
    
    settings = await cl.ChatSettings(settings_controls).send()
    await set_settings(settings)

@cl.on_message
async def main(message: cl.Message):
    """
    Entrypoint for handling user messages.
    """
    msg = cl.Message(content="")
    await msg.send()  # loading
    await msg.update()
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile]
    max_tokens = int(cl.user_session.get("max_tokens"))
    
    # Debug message elements
    if hasattr(message, "elements") and message.elements:
        for i, element in enumerate(message.elements):
            logger.debug(f"Element {i}: type={element.type}, name={getattr(element, 'name', 'N/A')}")
            if hasattr(element, "mime"):
                logger.debug(f"Element {i} mime type: {element.mime}")
            if hasattr(element, "path"):
                logger.debug(f"Element {i} path: {element.path}")
    
    # Process message contents
    images, docs, other_files = content_service.split_message_contents(message, model_info["id"])
    
    # Debug the processed contents
    logger.debug(f"Processed contents: images={images}, docs={docs}, other_files={other_files}")
    
    # Store content for later cleanup
    cl.user_session.set(
        "message_contents",
        images+docs
    )
    
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
        await cl.Message(content=f"Please provide a valid document or image or text. {suported_file_string}").send()
        content_service.delete_contents(images+docs)
        await msg.update()
        return
    
    # Log what we're sending to the model
    logger.debug(f"Sending to model: text={message.content}, images={len(images)}, docs={len(docs)}")
    
    api_usage = None
    try:
        response = await generate_conversation(cl.user_session.get("bedrock_runtime"), model_info["id"], message.content, max_tokens, images, docs)
        if cl.user_session.get("streaming"):
            stream = response.get('stream')
            if stream:
                # For tracking thinking content
                thinking_enabled = cl.user_session.get("thinking_enabled")
                thinking_manager = ThinkingService() if thinking_enabled else None
                thinking_step = None
                
                for event in stream:
                    if 'messageStart' in event:
                        logger.debug(f"\nRole: {event['messageStart']['role']}")

                    if 'contentBlockDelta' in event:
                        delta = event['contentBlockDelta'].get('delta', {})
                        
                        # Handle regular text content
                        if 'text' in delta:
                            logger.debug(delta['text'])
                            await msg.stream_token(delta['text'])
                        
                        # Handle reasoning content (thinking) if enabled
                        if thinking_enabled:
                            # Handle thinking text
                            # Handle thinking text and signature
                            if 'reasoningContent' in delta:
                                # Handle thinking text
                                if 'text' in delta['reasoningContent']:
                                    thinking_text = delta['reasoningContent']['text']
                                    thinking_manager.add_thinking(thinking_text)
                                    
                                    # Create thinking step if it doesn't exist
                                    if not thinking_step:
                                        thinking_step = cl.Step(
                                            name="Thinking 🤔",
                                            type="thinking"
                                        )
                                        await thinking_step.send()
                                    
                                    # For Chainlit 2.4.0, use the direct streaming approach
                                    # This is the most efficient way to stream tokens
                                    await thinking_step.stream_token(thinking_text)
                                    logger.debug(f"Thinking: {thinking_text}")
                                
                                # Handle signature directly from reasoningContent
                                if 'signature' in delta['reasoningContent']:
                                    signature = delta['reasoningContent']['signature']
                                    thinking_manager.set_signature(signature)
                                    logger.debug(f"Received thinking signature: {signature[:20]}...")
                            
                            # Handle redacted thinking
                            if 'redactedReasoningContent' in delta and 'data' in delta['redactedReasoningContent']:
                                redacted_data = delta['redactedReasoningContent']['data']
                                thinking_manager.add_redacted(redacted_data)
                                
                                # Create or update thinking step
                                if not thinking_step:
                                    thinking_step = cl.Step(
                                        name="Thinking 🤔",
                                        type="thinking"
                                    )
                                    await thinking_step.send()
                                
                                await thinking_step.stream_token("\n[Redacted thinking content]")
                                logger.debug("Received redacted thinking content")

                    if 'messageStop' in event:
                        logger.debug(f"\nStop reason: {event['messageStop']['stopReason']}")
                        
                        # Complete thinking step if it exists
                        if thinking_step:
                            await thinking_step.update()

                    if 'metadata' in event:
                        metadata = event['metadata']
                        if 'usage' in metadata:
                            logger.debug("\nToken usage")
                            logger.debug(f"Input tokens: {metadata['usage']['inputTokens']}")
                            logger.debug(
                                f":Output tokens: {metadata['usage']['outputTokens']}")
                            logger.debug(f":Total tokens: {metadata['usage']['totalTokens']}")
                            api_usage = {"inputTokenCount": metadata['usage']['inputTokens'],
                                        "outputTokenCount": metadata['usage']['outputTokens'],
                                        "invocationLatency": "not available in this API call",
                                        "firstByteLatency": "not available in this API call"}
                        if 'metrics' in event['metadata']:
                            logger.debug(
                                f"Latency: {metadata['metrics']['latencyMs']} milliseconds")
                            api_usage["invocationLatency"] = metadata['metrics']['latencyMs']
                
                # Get the message history
                message_history = cl.user_session.get("message_history")
                
                # Create the assistant message with properly formatted thinking blocks for API
                # Check if we should include reasoning content in message history
                chat_profile = cl.user_session.get("chat_profile")
                model_info = bedrock_models[chat_profile] if chat_profile else {}
                reasoning_config = model_info.get("reasoning", {})
                is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities")
                
                # For OpenAI models, check the user setting; for others, always include reasoning
                should_include_reasoning = True
                if is_openai_reasoning:
                    should_include_reasoning = cl.user_session.get("send_reasoning_back", False)
                
                if thinking_enabled and thinking_manager.has_thinking() and should_include_reasoning:
                    # Get thinking blocks formatted for API
                    api_blocks = thinking_manager.get_api_blocks()
                    
                    # Add to message history with properly formatted thinking blocks
                    message_history.append({
                        "role": "assistant", 
                        "content": [{"text": msg.content}] + api_blocks
                    })
                    
                    # Log what we're storing in message history
                    logger.debug(f"Stored assistant message with {len(api_blocks)} thinking blocks in message history")
                else:
                    # Add to message history without thinking blocks
                    message_history.append({
                        "role": "assistant", 
                        "content": [{"text": msg.content}]
                    })
                    if is_openai_reasoning and not should_include_reasoning:
                        logger.debug("OpenAI reasoning model: reasoning content excluded from history per user setting")
        else:

            # Get thinking enabled status
            thinking_enabled = cl.user_session.get("thinking_enabled")
            
            # Process the response
            text = ""
            thinking_manager = ThinkingService() if thinking_enabled else None
            
            # Check if response is None or doesn't have the expected structure
            if not response or 'output' not in response or 'message' not in response['output'] or 'content' not in response['output']['message']:
                error_msg = "Error: Failed to get a valid response from the model."
                logger.error(f"{error_msg} Response: {response}")
                msg.content = error_msg
                await msg.update()
                return
                
            # Extract content from the response
            for content_item in response['output']['message']["content"]:
                # Handle text content
                if 'text' in content_item:
                    text += content_item['text']
                
                # Handle thinking content in non-streaming mode
                elif thinking_enabled and 'reasoningContent' in content_item:
                    if 'reasoningText' in content_item['reasoningContent']:
                        thinking_text = content_item['reasoningContent']['reasoningText']['text']
                        thinking_signature = content_item['reasoningContent']['reasoningText'].get('signature')
                        
                        # Add to thinking manager
                        thinking_manager.add_thinking(thinking_text)
                        if thinking_signature:
                            thinking_manager.set_signature(thinking_signature)
                            logger.debug(f"Received thinking signature (non-streaming): {thinking_signature[:20]}...")
                        
                        # Create a thinking step to display in UI
                        thinking_step = cl.Step(
                            name="Thinking 🤔",
                            type="thinking"
                        )
                        await thinking_step.send()
                        await thinking_step.stream_token(thinking_text)
                        await thinking_step.update()
                        
                        logger.debug(f"Extracted thinking content (non-streaming): {thinking_text[:100]}...")
                
                # Handle redacted thinking content
                elif thinking_enabled and 'redactedReasoningContent' in content_item:
                    redacted_data = content_item['redactedReasoningContent']['data']
                    thinking_manager.add_redacted(redacted_data)
                    
                    # Create a thinking step for redacted content
                    thinking_step = cl.Step(
                        name="Thinking Process (Redacted)",
                        type="thinking"
                    )
                    await thinking_step.send()
                    await thinking_step.stream_token("[Redacted thinking content]")
                    await thinking_step.update()
                    
                    logger.debug("Extracted redacted thinking content (non-streaming)")
            
            # Update the message content
            msg.content = text
            
            # Get the message history
            message_history = cl.user_session.get("message_history")
            
            # Add to message history with properly formatted thinking blocks for API
            # Check if this model supports reasoning content in message history
            chat_profile = cl.user_session.get("chat_profile")
            model_info = bedrock_models[chat_profile] if chat_profile else {}
            reasoning_config = model_info.get("reasoning", {})
            # NOTE: OpenAI reasoning models don't support reasoning content in message history 
            # when using Bedrock Converse API. This limitation is specific to the Converse API -
            # reasoning content in history is likely supported with plain invoke() or OpenAI SDK directly.
            is_openai_reasoning = isinstance(reasoning_config, dict) and reasoning_config.get("openai_reasoning_modalities")
            
            # For OpenAI models, check the user setting; for others, always include reasoning
            should_include_reasoning = True
            if is_openai_reasoning:
                should_include_reasoning = cl.user_session.get("send_reasoning_back", False)
            
            if thinking_enabled and thinking_manager and thinking_manager.has_thinking() and should_include_reasoning:
                # Get thinking blocks formatted for API
                api_blocks = thinking_manager.get_api_blocks()
                
                # Add to message history with properly formatted thinking blocks
                message_history.append({
                    "role": "assistant",
                    "content": [{"text": text}] + api_blocks
                })
                
                logger.debug(f"Stored assistant message with {len(api_blocks)} thinking blocks in message history (non-streaming)")
            else:
                # Add to message history without thinking blocks
                message_history.append({
                    "role": "assistant",
                    "content": [{"text": text}]
                })
                if is_openai_reasoning and not should_include_reasoning:
                    logger.debug("OpenAI reasoning model: reasoning content excluded from history per user setting (non-streaming)")
            
            # Extract usage information
            api_usage = {
                "inputTokenCount": response["usage"]["inputTokens"],
                "outputTokenCount": response["usage"]["outputTokens"],
                "invocationLatency": response['metrics']['latencyMs'],
                "firstByteLatency": "not available in this API call"
            }
            
        if api_usage: 
            invocation_cost = api_usage["inputTokenCount"]/1000 * model_info["cost"]["input_1k_price"] + api_usage["outputTokenCount"]/1000 * model_info["cost"]["output_1k_price"]
            total_cost = cl.user_session.get("total_cost") + invocation_cost
            cl.user_session.set("total_cost", total_cost)
            logger.debug(f"Invocation cost: {invocation_cost}")
            logger.debug(f"Total chat cost: {total_cost}")
        else:
            logger.debug(f"api usage not defined")

        if cl.user_session.get("costs"):
            precision = cl.user_session.get("precision")  # You can change this value to adjust the precision
            s_invocation_cost = f"{invocation_cost:.{precision}f}".rstrip('0') or '0.00'
            s_total_cost = f"{total_cost:.{precision}f}".rstrip('0') or '0.00'
            elements = [
                cl.Text(name="Invocation cost", content=f"Invocation cost: {s_invocation_cost}$", display="inline"),
                cl.Text(name="Chat cost", content=f"Total chat cost: {s_total_cost}$", display="inline")
            ]
            await cl.Message(
            content="",
            elements=elements,
            ).send()
            
        await msg.update()

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        
@cl.on_chat_end
def on_chat_end():
    # sometimes chainlit does not automatically delete the uploaded files. 
    # So we are removing all the files to garantee the privacy
    message_contents = cl.user_session.get("message_contents")
    content_service.delete_contents(message_contents, True)