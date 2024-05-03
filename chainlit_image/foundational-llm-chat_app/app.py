import chainlit as cl
from typing import Dict, Optional
import json
import boto3
from chainlit.input_widget import Switch, Slider, TextInput
from botocore.exceptions import ClientError
from system_strings import suported_file_string
from content_management_utils import logger, verify_content, split_message_contents, delete_contents
from massages_utils import create_content, create_image_content
from config import my_aws_config as my_config, system_prompt, bedrock_models

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user

def multi_modal_prompt(bedrock_runtime=None, model_id="anthropic.claude-3-sonnet-20240229-v1:0", input_text=None, max_tokens=1000, images=None):
    """
    Streams the response from a multimodal prompt.
    Args:
        bedrock_runtime: The Amazon Bedrock boto3 client.
        model_id (str): The model ID to use.
        input_text (str) : The prompt text
        image (str) : The path to  an image that you want in the prompt.
        max_tokens (int) : The maximum  number of tokens to generate.
    Returns:
        None.
    """
    temperature = float(cl.user_session.get("temperature"))
    message_history = cl.user_session.get("message_history")
    if input_text is None and images is None:
        raise ValueError("input_text or images_path must be provided")
    images_body = None
    if images:
        images_body = create_image_content(images)
    new_user_content = create_content(input_text, images_body)
    message_history.append({"role": "user", "content": new_user_content})
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": cl.user_session.get("system_prompt"),
        "messages": message_history,
        "temperature": temperature,
        # "top_p": 0.999
    })
    if cl.user_session.get("streaming"):
        return bedrock_runtime.invoke_model_with_response_stream(body=body, modelId=model_id)
    else:
        return bedrock_runtime.invoke_model(body=body, modelId=model_id)

@cl.on_settings_update
def set_settings(settings):
    cl.user_session.set(
        "streaming",
        settings["streaming"],
    )
    cl.user_session.set(
        "temperature",
        settings["temperature"],
    )
    cl.user_session.set(
        "max_tokens",
        settings["max_tokens"],
    )
    cl.user_session.set(
        "costs",
        settings["costs"],
    ),
    cl.user_session.set(
        "precision",
        settings["precision"],
    )
    cl.user_session.set(
        "system_prompt",
        settings["system_prompt"])
    return

@cl.on_chat_start
async def start():
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
    cl.user_session.set(
        "system_prompt",
        system_prompt
    )
    try: 
        cl.user_session.set("bedrock_runtime", boto3.client('bedrock-runtime', config=my_config))
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occured: " +
              format(message))

    settings = await cl.ChatSettings(
            [
                Switch(id="streaming", label="Streaming", initial=True),
                TextInput(id="system_prompt", label="System Prompt", initial=cl.user_session.get("system_prompt")),
                Slider(
                    id="temperature",
                    label="Temperature",
                    initial=1,
                    min=0,
                    max=1,
                    step=0.1,
                ),
                Slider(
                    id="max_tokens",
                    label="Maximum tokens",
                    initial=1000,
                    min=1,
                    max=4096,
                    step=1,
                ),
                Switch(id="costs", label="Show costs in the answer", initial=False),
                Slider(id="precision", label="Digit Precision of costs", initial=4, min=1, max=10, step=1)
            ]
        ).send()
    set_settings(settings)

@cl.set_chat_profiles
async def chat_profile():
    profiles = []
    
    for key in bedrock_models.keys():
        is_default = None
        if "default" in bedrock_models[key]:
            is_default = bedrock_models[key]["default"]
        profiles.append(cl.ChatProfile(name=key, 
                                       markdown_description=f"The underlying LLM model is *Claude 3 {key}*.", 
                                       icon=f"./public/{key.lower()}.png",
                                       default = is_default if is_default else False))
    return profiles

@cl.on_message
async def main(message: cl.Message):
    # Your custom logic goes here...
    # Send a response back to the user
    """
    Entrypoint for Anthropic Claude Sonnet multimodal prompt example.
    """
    msg = cl.Message(content="")
    await msg.send()  # loading
    await msg.update()
    chat_profile = cl.user_session.get("chat_profile")
    model_info = bedrock_models[chat_profile]
    max_tokens = int(cl.user_session.get("max_tokens"))
    message_history = cl.user_session.get("message_history")
    images, other_files = split_message_contents(message)
    cl.user_session.set(
        "message_contents",
        images
    )
    # check if images are true images
    # check dimension of image of each image and discard
    if len(other_files) > 0:
        name_string = ", ".join([other["name"] for other in other_files])
        await cl.Message(content=f"The files {name_string} is not supported. Not considering it").send()
        delete_contents(other_files)
    if not verify_content(message.content, images):
        await cl.Message(content=f"Please provide a valid image or text. {suported_file_string}").send()
        delete_contents(images)
    try:
        response = multi_modal_prompt(cl.user_session.get("bedrock_runtime"), model_info["id"], message.content, max_tokens, images)
        if cl.user_session.get("streaming"):
            for event in response.get("body"):
                chunk = json.loads(event["chunk"]["bytes"])
                if chunk['type'] == 'message_stop':
                    api_usage = {"inputTokenCount": chunk['amazon-bedrock-invocationMetrics']["inputTokenCount"],
                                "outputTokenCount": chunk['amazon-bedrock-invocationMetrics']["outputTokenCount"],
                                "invocationLatency": chunk['amazon-bedrock-invocationMetrics']["invocationLatency"],
                                "firstByteLatency": chunk['amazon-bedrock-invocationMetrics']["firstByteLatency"]}
                if chunk['type'] == 'content_block_delta':
                    if chunk['delta']['type'] == 'text_delta':
                        await msg.stream_token(chunk['delta']['text'])
            message_history.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})
        else:
            response_object = json.loads(response.get('body').read())
            text = response_object["content"][0]["text"]
            msg.content = text
            message_history.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})
            api_usage = {"inputTokenCount": response_object["usage"]["input_tokens"],
                         "outputTokenCount": response_object["usage"]["output_tokens"],
                         "invocationLatency": "not available in this API call",
                         "firstByteLatency": "not available in this API call"}
        if api_usage: 
            invocation_cost = api_usage["inputTokenCount"]/1000 * model_info["cost"]["input_1k_price"] + api_usage["outputTokenCount"]/1000 * model_info["cost"]["output_1k_price"]
            total_cost = cl.user_session.get("total_cost") + invocation_cost
            cl.user_session.set("total_cost", total_cost)
            logger.info(f"Invocation cost: {invocation_cost}")
            logger.info(f"Total chat cost: {total_cost}")
        else:
            logger.info(f"api usage not defined")

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
    delete_contents(message_contents, True)
