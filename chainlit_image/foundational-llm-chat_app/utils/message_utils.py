"""
Utilities for handling messages.
"""

from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


def create_content(
    text: Optional[str],
    images: Optional[List[Dict[str, Any]]],
    docs: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Create content for a message.

    Args:
        text: The text content.
        images: List of images.
        docs: List of documents.

    Returns:
        A list of content items.
    """
    content = []

    # Add image content if provided
    if images:
        for image in images:
            content.append(image)

    # Add document content if provided
    if docs:
        for doc in docs:
            content.append(doc)

    # Add text content if provided (add last as in original app)
    if text:
        content.append({"text": text})

    return content


def create_image_content(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create image content for a message.

    Args:
        images: List of images.

    Returns:
        A list of image content items.
    """
    image_content = []

    for image in images:
        try:
            logger.debug(f"Processing image: {image['name']} ({image['path']})")
            with open(image["path"], "rb") as f:
                image_data = f.read()

            # Format the image content according to Bedrock API requirements
            # Using the format from the original app
            image_content.append(
                {
                    "image": {
                        "format": get_file_extension(image["type"]),
                        "source": {"bytes": image_data},
                    }
                }
            )
            logger.debug(
                f"Successfully encoded image: {image['name']} ({image['type']})"
            )
        except Exception as e:
            logger.error(f"Error creating image content for {image['path']}: {e}")

    return image_content


def get_file_extension(file_type):
    """
    Get the file extension from the MIME type.

    Args:
        file_type: The MIME type.

    Returns:
        The file extension.
    """
    if not file_type:
        return ""

    file_extension = file_type.split("/")[1] if "/" in file_type else file_type

    # Map MIME types to file extensions
    extension_map = {
        "jpg": "jpeg",
        "jpeg": "jpeg",
        "png": "png",
        "gif": "gif",
        "webp": "webp",
        "vnd.ms-excel": "xls",
        "vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "msword": "doc",
        "plain": "txt",
        "markdown": "md",
        "html": "html",
        "pdf": "pdf",
        "csv": "csv",
    }

    return extension_map.get(file_extension, file_extension)


def create_doc_content(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create document content for a message.

    Args:
        docs: List of documents.

    Returns:
        A list of document content items.
    """
    doc_content = []

    for doc in docs:
        try:
            logger.debug(f"Processing document: {doc['name']} ({doc['path']})")

            # Determine document format from file type or extension
            doc_format = get_file_extension(doc["type"]) if doc["type"] else ""
            if not doc_format:
                # Try to infer format from file extension
                if doc["name"].lower().endswith(".txt"):
                    doc_format = "txt"
                elif doc["name"].lower().endswith(".pdf"):
                    doc_format = "pdf"
                elif doc["name"].lower().endswith(".doc"):
                    doc_format = "doc"
                elif doc["name"].lower().endswith(".docx"):
                    doc_format = "docx"
                elif doc["name"].lower().endswith(".csv"):
                    doc_format = "csv"
                elif doc["name"].lower().endswith(".xls"):
                    doc_format = "xls"
                elif doc["name"].lower().endswith(".xlsx"):
                    doc_format = "xlsx"
                elif doc["name"].lower().endswith((".html", ".htm")):
                    doc_format = "html"
                elif doc["name"].lower().endswith(".md"):
                    doc_format = "md"
                else:
                    doc_format = "txt"  # Default to txt if unknown

            logger.debug(f"Document format determined as: {doc_format}")

            # Using the format from the original app
            with open(doc["path"], "rb") as f:
                doc_data = f.read()

            doc_content.append(
                {
                    "document": {
                        "name": sanitize_filename(doc["name"]),
                        "format": doc_format,
                        "source": {"bytes": doc_data},
                    }
                }
            )
            logger.debug(f"Successfully encoded document: {doc['name']} ({doc_format})")

        except Exception as e:
            logger.error(f"Error creating document content for {doc['path']}: {e}")

    return doc_content


def sanitize_filename(filename):
    """
    Sanitize a filename.

    Args:
        filename: The filename to sanitize.

    Returns:
        The sanitized filename.
    """
    # Remove consecutive whitespace characters
    filename = re.sub(r"\s+", " ", filename)

    # Replace consecutive hyphens with a single hyphen
    filename = re.sub(r"-+", "-", filename)

    # Replace any remaining invalid characters with an underscore
    filename = re.sub(r"[^a-zA-Z0-9\s\-\(\)\[\]]", "_", filename)

    return filename


def extract_and_process_prompt(prompt_object: Dict[str, Any]) -> str:
    """
    Extract and process a prompt from a prompt object.

    Args:
        prompt_object: The prompt object.

    Returns:
        The processed prompt text.
    """
    from datetime import datetime, timezone

    try:
        # Check if the prompt object has variants
        if "variants" in prompt_object and prompt_object["variants"]:
            variant = prompt_object["variants"][0]

            # Check if the variant has templateConfiguration
            if (
                "templateConfiguration" in variant
                and "text" in variant["templateConfiguration"]
            ):
                # Extract the prompt text
                prompt_text = variant["templateConfiguration"]["text"]["text"]

                # Extract input variables if they exist
                if "inputVariables" in variant["templateConfiguration"]["text"]:
                    input_variables = variant["templateConfiguration"]["text"][
                        "inputVariables"
                    ]

                    # Get current date and time
                    now = datetime.now(timezone.utc)
                    today = now.strftime(
                        "%Y-%m-%d"
                    )  # Current date in YYYY-MM-DD format
                    utc_time = now.strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )  # Current time in YYYY-MM-DD HH:MM:SS UTC format

                    # Process variables
                    for var in input_variables:
                        var_name = var["name"]
                        if var_name == "TODAY":
                            prompt_text = prompt_text.replace("{{TODAY}}", today)
                        elif var_name == "UTC_TIME":
                            prompt_text = prompt_text.replace("{{UTC_TIME}}", utc_time)
                        elif var_name == "AI":
                            # For now, we'll leave {{AI}} as is, but you can replace it if needed
                            pass
                        else:
                            # For other variables, use a default message
                            logger.warning(
                                f"Unsupported variable in prompt: {var_name}"
                            )
                            prompt_text = "Your system prompt is not working correctly due to the presence of variables that are not used. We support: TODAY, UTC_TIME, AI"

                return prompt_text
            elif "content" in variant:
                # If there's direct content, use that
                return variant["content"]
            else:
                logger.warning(f"No templateConfiguration or content found in variant")
                return ""
        else:
            logger.warning(
                f"No variants found in prompt object: {prompt_object.keys()}"
            )
            return ""
    except Exception as e:
        logger.error(f"Error extracting prompt: {e}")
        return ""
