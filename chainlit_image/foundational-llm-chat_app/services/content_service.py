"""
Service for handling content (images, documents, etc.).
"""

from typing import Dict, Any, List, Tuple, Optional
import os
import logging

logger = logging.getLogger(__name__)


class ContentService:
    """Service for handling content (images, documents, etc.)."""

    def __init__(
        self, max_chars: Optional[int] = None, max_size_mb: Optional[float] = None
    ):
        """
        Initialize the content service.

        Args:
            max_chars: Maximum number of characters allowed.
            max_size_mb: Maximum content size in MB.
        """
        self.max_chars = max_chars
        self.max_size_mb = max_size_mb

    def verify_content(
        self,
        text: Optional[str],
        images: List[Dict[str, Any]],
        docs: List[Dict[str, Any]],
    ) -> bool:
        """
        Verify that the content is valid.

        Args:
            text: The text content.
            images: List of images.
            docs: List of documents.

        Returns:
            True if the content is valid, False otherwise.
        """
        # Check if there is any content
        if not text and not images and not docs:
            return False

        # Check text length if max_chars is set
        if text and self.max_chars and len(text) > self.max_chars:
            logger.warning(
                f"Text exceeds maximum length: {len(text)} > {self.max_chars}"
            )
            return False

        # Verify images
        if not self.verify_image_content(images):
            logger.warning("Image content verification failed")
            return False

        # Verify documents
        if not self.verify_doc_content(docs):
            logger.warning("Document content verification failed")
            return False

        return True

    def verify_image_content(self, images: List[Dict[str, Any]]) -> bool:
        """
        Verify that the image content is valid.

        Args:
            images: List of images.

        Returns:
            True if the image content is valid, False otherwise.
        """
        if len(images) == 0:
            return True

        try:
            from PIL import Image
        except ImportError:
            logger.warning("PIL not installed, skipping image verification")
            return True

        for image in images:
            if not os.path.isfile(image["path"]):
                logger.warning(f"Image file not found: {image['path']}")
                return False
            else:
                try:
                    with Image.open(image["path"]) as img:
                        img.verify()
                        if img.format not in ["PNG", "JPEG", "GIF", "WEBP"]:
                            logger.warning(f"Unsupported image format: {img.format}")
                            return False
                        size = os.stat(image["path"]).st_size / (1024 * 1024)
                        if self.max_size_mb and size > self.max_size_mb:
                            logger.warning(
                                f"Image exceeds maximum size: {size} MB > {self.max_size_mb} MB"
                            )
                            return False
                except Exception as e:
                    logger.warning(f"Error verifying image: {e}")
                    return False
        return True

    def verify_doc_content(self, docs: List[Dict[str, Any]]) -> bool:
        """
        Verify that the document content is valid.

        Args:
            docs: List of documents.

        Returns:
            True if the document content is valid, False otherwise.
        """
        if len(docs) == 0:
            return True

        for doc in docs:
            if not os.path.isfile(doc["path"]):
                logger.warning(f"Document file not found: {doc['path']}")
                return False
            else:
                try:
                    size = os.stat(doc["path"]).st_size / (1024 * 1024)
                    if self.max_size_mb and size > self.max_size_mb:
                        logger.warning(
                            f"Document exceeds maximum size: {size} MB > {self.max_size_mb} MB"
                        )
                        return False
                except Exception as e:
                    logger.warning(f"Error verifying document: {e}")
                    return False
        return True

    def split_message_contents(
        self, message: Any, model_id: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split message contents into images, documents, and other files.

        Args:
            message: The message containing files.
            model_id: The model ID to use.

        Returns:
            A tuple of (images, documents, other_files).
        """
        images = []
        docs = []
        other_files = []

        # Process files if available
        if hasattr(message, "elements") and message.elements:
            logger.debug(f"Message has {len(message.elements)} elements")
            for element in message.elements:
                # Debug element attributes
                logger.debug(f"Element attributes: {dir(element)}")
                logger.debug(f"Element type: {element.type}")

                # Handle both file and image element types
                if element.type == "file" or element.type == "image":
                    file_path = element.path
                    file_name = element.name
                    file_size = os.path.getsize(file_path)

                    # Get MIME type, default to inferring from file extension if not available
                    file_type = getattr(element, "mime", "")
                    if not file_type:
                        # Try to infer MIME type from file extension
                        if file_name.lower().endswith((".txt")):
                            file_type = "text/plain"
                        elif file_name.lower().endswith((".pdf")):
                            file_type = "application/pdf"
                        elif file_name.lower().endswith((".doc")):
                            file_type = "application/msword"
                        elif file_name.lower().endswith((".docx")):
                            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        elif file_name.lower().endswith((".xls")):
                            file_type = "application/vnd.ms-excel"
                        elif file_name.lower().endswith((".xlsx")):
                            file_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        elif file_name.lower().endswith((".csv")):
                            file_type = "text/csv"
                        elif file_name.lower().endswith((".html", ".htm")):
                            file_type = "text/html"
                        elif file_name.lower().endswith((".md")):
                            file_type = "text/markdown"
                        elif file_name.lower().endswith((".jpg", ".jpeg")):
                            file_type = "image/jpeg"
                        elif file_name.lower().endswith((".png")):
                            file_type = "image/png"
                        elif file_name.lower().endswith((".gif")):
                            file_type = "image/gif"
                        elif file_name.lower().endswith((".webp")):
                            file_type = "image/webp"

                    logger.debug(f"Processing file/image: {file_name} ({file_type})")

                    # Check if the file is an image
                    if file_type.startswith("image/") or element.type == "image":
                        images.append(
                            {
                                "path": file_path,
                                "name": file_name,
                                "type": file_type
                                or "image/png",  # Default to PNG if no MIME type
                                "size": file_size,
                            }
                        )
                        logger.debug(f"Added image: {file_name}")
                    # Check if the file is a document
                    elif file_type in [
                        "application/pdf",
                        "text/plain",
                        "text/html",
                        "text/markdown",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/msword",
                        "application/vnd.ms-excel",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "text/csv",
                    ] or file_name.lower().endswith(
                        (
                            ".txt",
                            ".pdf",
                            ".doc",
                            ".docx",
                            ".xls",
                            ".xlsx",
                            ".csv",
                            ".html",
                            ".htm",
                            ".md",
                        )
                    ):
                        docs.append(
                            {
                                "path": file_path,
                                "name": file_name,
                                "type": file_type
                                or "text/plain",  # Default to text/plain if no MIME type
                                "size": file_size,
                            }
                        )
                        logger.debug(f"Added document: {file_name}")
                    # Other file types
                    else:
                        other_files.append(
                            {
                                "path": file_path,
                                "name": file_name,
                                "type": file_type,
                                "size": file_size,
                            }
                        )
                        logger.debug(f"Added other file: {file_name}")

        logger.debug(
            f"Split message contents: {len(images)} images, {len(docs)} documents, {len(other_files)} other files"
        )
        return images, docs, other_files

    def delete_contents(
        self, contents: List[Dict[str, Any]], force: bool = False
    ) -> None:
        """
        Delete content files.

        Args:
            contents: List of content items to delete.
            force: Force deletion even if the file is not temporary.
        """
        for content in contents:
            if "path" in content:
                path = content["path"]

                # Only delete temporary files unless force is True
                if force or path.startswith("/tmp/"):
                    try:
                        os.remove(path)
                        logger.debug(f"Deleted file: {path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {path}: {e}")
