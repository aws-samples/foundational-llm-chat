import os
import json

aws_region = os.environ.get('AWS_REGION')
if not aws_region:
    raise Exception('AWS_REGION environment variable not set')

my_aws_config = {
    "region_name": aws_region
}

system_prompt = "You are an assistant"
if os.environ.get('DEFAULT_SYSTEM_PROMPT'):
    system_prompt = os.environ.get('DEFAULT_SYSTEM_PROMPT')

MAX_CHARACHERS = None if (not os.getenv("MAX_CHARACHERS") or os.getenv("MAX_CHARACHERS") == "None") else int(os.getenv("MAX_CHARACHERS"))
MAX_CONTENT_SIZE_MB = None if (not os.getenv("MAX_CONTENT_SIZE_MB") or os.getenv("MAX_CONTENT_SIZE_MB") == "None") else float(os.getenv("MAX_CONTENT_SIZE_MB"))

bedrock_models = None if not os.getenv("BEDROCK_MODELS") else json.loads(os.getenv("BEDROCK_MODELS"))