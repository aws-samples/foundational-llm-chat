"""
Service for handling thinking content.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ThinkingService:
    """Service for handling thinking content."""

    def __init__(self):
        """
        Initialize the thinking service.
        """
        self.thinking_text = ""
        self.signature = None
        self.redacted_data = []

    def add_thinking(self, text: str) -> None:
        """
        Add thinking text.

        Args:
            text: The thinking text to add.
        """
        self.thinking_text += text

    def set_signature(self, signature: str) -> None:
        """
        Set the signature.

        Args:
            signature: The signature to set.
        """
        self.signature = signature

    def add_redacted(self, data: str) -> None:
        """
        Add redacted data.

        Args:
            data: The redacted data to add.
        """
        self.redacted_data.append(data)

    def has_thinking(self) -> bool:
        """
        Check if there is thinking content.

        Returns:
            True if there is thinking content, False otherwise.
        """
        return bool(self.thinking_text)

    def get_api_blocks(self) -> List[Dict[str, Any]]:
        """
        Get thinking blocks formatted for API.

        Returns:
            A list of thinking blocks.
        """
        blocks = []

        # Add thinking block if there is thinking content
        if self.thinking_text:
            thinking_block = {
                "reasoningContent": {"reasoningText": {"text": self.thinking_text}}
            }

            # Add signature if available
            if self.signature:
                thinking_block["reasoningContent"]["reasoningText"]["signature"] = (
                    self.signature
                )

            blocks.append(thinking_block)

        # Add redacted blocks if there are any
        for data in self.redacted_data:
            blocks.append({"redactedReasoningContent": {"data": data}})

        return blocks
