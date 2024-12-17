import chainlit as cl
from typing import Dict, Optional
import boto3
from botocore.config import Config
from chainlit.input_widget import Switch, Slider, TextInput
from botocore.exceptions import ClientError
from system_strings import suported_file_string
from config import my_aws_config as my_config, system_prompt_list, bedrock_models, DYNAMODB_DATA_LAYER_NAME, S3_DATA_LAYER_NAME
from content_management_utils import logger, verify_content, split_message_contents, delete_contents
from massages_utils import create_content, create_image_content, create_doc_content, extract_and_process_prompt


# TODO: add data persistance when fixed by chainlit
# import chainlit.data as cl_data
# from chainlit.data.dynamodb import DynamoDBDataLayer
# from chainlit.data.storage_clients import S3StorageClient
# from chainlit.types import ThreadDict

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user

# TODO: add data persistance when fixed by chainlit
# import chainlit.data as cl_data
# from chainlit.data.dynamodb import DynamoDBDataLayer
# from chainlit.data.storage_clients import S3StorageClient
# if(S3_DATA_LAYER_NAME and DYNAMODB_DATA_LAYER_NAME):
#     storage_client = S3StorageClient(bucket=S3_DATA_LAYER_NAME)
#     cl_data._data_layer = DynamoDBDataLayer(table_name=DYNAMODB_DATA_LAYER_NAME, storage_provider=storage_client)

def generate_conversation(bedrock_client=None, model_id="anthropic.claude-3-sonnet-20240229-v1:0", input_text=None, max_tokens=1000, images=None, docs=None):
    """
    Sends messages to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        messages (JSON) : The messages to send to the model.

    Returns:
        response (JSON): The conversation that the model generated.

    """
    temperature = float(cl.user_session.get("temperature"))
    message_history = cl.user_session.get("message_history")
    if input_text is None and images is None:
        raise ValueError("input_text or images_path must be provided")
    images_body = None
    if images:
        images_body = create_image_content(images)
    docs_body = None
    if docs:
        docs_body = create_doc_content(docs)
    new_user_content = create_content(input_text, images_body, docs_body)
    message_history.append({"role": "user", "content": new_user_content})

    # Base inference parameters to use.
    inference_config = {"temperature": temperature}

    # Additional inference parameters to use.
    additional_model_fields = {}

    if cl.user_session.get("streaming"):
        try: 
            return  bedrock_client.converse_stream(
            modelId=model_id,
            messages=message_history,
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
            messages=message_history,
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
        [{"text": settings["system_prompt"]}])
    return

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
    try:
        bedrock_client_config = Config(**my_config)
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
    try:
        bedrock_agent_client_config = Config(**my_config)
        cl.user_session.set("bedrock_agent_runtime", boto3.client('bedrock-agent', config=bedrock_agent_client_config))
        system_prompt_object = cl.user_session.get("bedrock_agent_runtime").get_prompt(promptIdentifier=system_prompt_list[chat_profile].get("id"), promptVersion=system_prompt_list[chat_profile].get("version"))
        system_prompt = extract_and_process_prompt(system_prompt_object)
    except ClientError as err:
        system_prompt = ""
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occured: " +
              format(message))
    cl.user_session.set(
        "system_prompt",
        [{"text": system_prompt}]
    )
    settings = await cl.ChatSettings(
            [
                Switch(id="streaming", label="Streaming", initial=True),
                TextInput(id="system_prompt", label="System Prompt", initial=cl.user_session.get("system_prompt")[0]["text"]),
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
    images, docs, other_files = split_message_contents(message, model_info["id"])
    cl.user_session.set(
        "message_contents",
        images+docs
    )
    # check if images are true images
    # check dimension of image of each image and discard
    message_info = None
    if len(other_files) > 0:
        name_string = ", ".join([other["name"] for other in other_files])
        message_info = f"The files {name_string} is not supported by the model you are using: {model_info}. Not considering it"
        elements = [
                cl.Text(name="Warning", content=message_info, display="inline"),
            ]
        await cl.Message(
        content="",
        elements=elements,
        ).send()
        delete_contents(other_files)
    if not verify_content(message.content, images, docs):
        await cl.Message(content=f"Please provide a valid document or image or text. {suported_file_string}").send()
        delete_contents(images+docs)
    api_usage = None
    try:
        response = generate_conversation(cl.user_session.get("bedrock_runtime"), model_info["id"], message.content, max_tokens, images, docs)
        if cl.user_session.get("streaming"):
            stream = response.get('stream')
            if stream:
                for event in stream:
                    if 'messageStart' in event:
                        logger.info(f"\nRole: {event['messageStart']['role']}")

                    if 'contentBlockDelta' in event:
                        logger.info(event['contentBlockDelta']['delta']['text'])
                        await msg.stream_token(event['contentBlockDelta']['delta']['text'])

                    if 'messageStop' in event:
                        logger.info(f"\nStop reason: {event['messageStop']['stopReason']}")

                    if 'metadata' in event:
                        metadata = event['metadata']
                        if 'usage' in metadata:
                            logger.info("\nToken usage")
                            logger.info(f"Input tokens: {metadata['usage']['inputTokens']}")
                            logger.info(
                                f":Output tokens: {metadata['usage']['outputTokens']}")
                            logger.info(f":Total tokens: {metadata['usage']['totalTokens']}")
                            api_usage = {"inputTokenCount": metadata['usage']['inputTokens'],
                                        "outputTokenCount": metadata['usage']['outputTokens'],
                                        "invocationLatency": "not available in this API call",
                                        "firstByteLatency": "not available in this API call"}
                        if 'metrics' in event['metadata']:
                            logger.info(
                                f"Latency: {metadata['metrics']['latencyMs']} milliseconds")
                            api_usage["invocationLatency"] = metadata['metrics']['latencyMs']
                message_history.append({"role": "assistant", "content": [{"text": msg.content}]})
        else:
            text = ""
            for t in response['output']['message']["content"]:
                text += t["text"]
            msg.content = text
            message_history.append(response['output']['message'])
            api_usage = {"inputTokenCount": response["usage"]["inputTokens"],
                         "outputTokenCount": response["usage"]["outputTokens"],
                         "invocationLatency": response['metrics']['latencyMs'],
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
