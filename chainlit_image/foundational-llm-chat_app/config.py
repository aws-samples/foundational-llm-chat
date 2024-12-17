import os
import json

aws_region = os.environ.get('AWS_REGION')
if not aws_region:
    raise Exception('AWS_REGION environment variable not set')

my_aws_config = {
    "region_name": aws_region
}

# Load the system prompt list from the environment variable
system_prompt_list = {}
if os.environ.get('SYSTEM_PROMPT_LIST'):
    try:
        system_prompt_list = json.loads(os.environ.get('SYSTEM_PROMPT_LIST'))
    except json.JSONDecodeError:
        print("Error decoding SYSTEM_PROMPT_LIST JSON")

MAX_CHARACHERS = None if (not os.getenv("MAX_CHARACHERS") or os.getenv("MAX_CHARACHERS") == "None") else int(os.getenv("MAX_CHARACHERS"))
MAX_CONTENT_SIZE_MB = None if (not os.getenv("MAX_CONTENT_SIZE_MB") or os.getenv("MAX_CONTENT_SIZE_MB") == "None") else float(os.getenv("MAX_CONTENT_SIZE_MB"))

DYNAMODB_DATA_LAYER_NAME = None if (not os.getenv("DYNAMODB_DATA_LAYER_NAME") or os.getenv("DYNAMODB_DATA_LAYER_NAME") == "None") else str(os.getenv("DYNAMODB_DATA_LAYER_NAME"))
S3_DATA_LAYER_NAME = None if (not os.getenv("S3_DATA_LAYER_NAME") or os.getenv("S3_DATA_LAYER_NAME") == "None") else str(os.getenv("S3_DATA_LAYER_NAME"))

bedrock_models = None if not os.getenv("BEDROCK_MODELS") else json.loads(os.getenv("BEDROCK_MODELS"))
