"""
Application settings and configuration management.
"""

import os
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Settings:
    """Application settings manager"""

    @staticmethod
    def load_aws_config() -> Dict[str, str]:
        """Load AWS configuration"""
        aws_region = os.environ.get("AWS_REGION")
        if not aws_region:
            raise ValueError("AWS_REGION environment variable not set")

        return {"region_name": aws_region}

    @staticmethod
    def load_system_prompts() -> Dict[str, Any]:
        """Load system prompts configuration"""
        system_prompt_list = {}
        if os.environ.get("SYSTEM_PROMPT_LIST"):
            try:
                system_prompt_list = json.loads(os.environ.get("SYSTEM_PROMPT_LIST"))
                logger.debug(f"Loaded {len(system_prompt_list)} system prompts")
            except json.JSONDecodeError:
                logger.error("Error decoding SYSTEM_PROMPT_LIST JSON")

        return system_prompt_list

    @staticmethod
    def load_content_limits() -> Dict[str, Any]:
        """Load content size limits"""
        return {
            "max_chars": None
            if (
                not os.getenv("MAX_CHARACHERS") or os.getenv("MAX_CHARACHERS") == "None"
            )
            else int(os.getenv("MAX_CHARACHERS")),
            "max_content_size_mb": None
            if (
                not os.getenv("MAX_CONTENT_SIZE_MB")
                or os.getenv("MAX_CONTENT_SIZE_MB") == "None"
            )
            else float(os.getenv("MAX_CONTENT_SIZE_MB")),
        }

    @staticmethod
    def load_data_layer_config() -> Dict[str, Optional[str]]:
        """Load data layer configuration"""
        return {
            "dynamodb_table": None
            if (
                not os.getenv("DYNAMODB_DATA_LAYER_NAME")
                or os.getenv("DYNAMODB_DATA_LAYER_NAME") == "None"
            )
            else str(os.getenv("DYNAMODB_DATA_LAYER_NAME")),
            "s3_bucket": None
            if (
                not os.getenv("S3_DATA_LAYER_NAME")
                or os.getenv("S3_DATA_LAYER_NAME") == "None"
            )
            else str(os.getenv("S3_DATA_LAYER_NAME")),
        }

    @staticmethod
    def load_bedrock_models() -> Dict[str, Any]:
        """Load Bedrock models configuration"""
        if not os.getenv("BEDROCK_MODELS"):
            logger.error("BEDROCK_MODELS environment variable not set")
            return {}

        try:
            models = json.loads(os.getenv("BEDROCK_MODELS"))
            logger.debug(f"Loaded {len(models)} Bedrock models")
            return models
        except json.JSONDecodeError:
            logger.error("Error decoding BEDROCK_MODELS JSON")
            return {}
