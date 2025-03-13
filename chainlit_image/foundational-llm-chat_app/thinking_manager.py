"""
Thinking block management for Claude 3.7 Sonnet reasoning capabilities.
"""
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ThinkingBlockManager:
    """Manages thinking blocks for Claude 3.7 Sonnet reasoning."""
    
    def __init__(self):
        """Initialize the thinking block manager."""
        self.current_thinking = {
            "text": "",
            "signature": None
        }
        self.current_redacted = None
        
    def add_thinking(self, text):
        """
        Add thinking text to the current thinking block.
        
        Args:
            text (str): The thinking text to add
        """
        self.current_thinking["text"] += text
        logger.debug(f"Added thinking text: {text[:50]}...")
        
    def set_signature(self, signature):
        """
        Set the signature for the current thinking block.
        
        Args:
            signature (str): The cryptographic signature from Claude
        """
        self.current_thinking["signature"] = signature
        logger.debug(f"Thinking signature received and stored: {signature[:20]}...")
        
    def add_redacted(self, data):
        """
        Add redacted thinking data.
        
        Args:
            data (str): The encrypted redacted thinking data
        """
        self.current_redacted = {
            "type": "redacted_thinking",
            "data": data
        }
        logger.debug("Redacted thinking data received and stored")
        
    def get_blocks(self):
        """
        Get all thinking blocks in the correct format for display.
        
        Returns:
            list: List of thinking blocks in the format for UI display
        """
        blocks = []
        if self.current_thinking["text"]:
            thinking_block = {
                "type": "thinking",
                "thinking": self.current_thinking["text"]
            }
            if self.current_thinking["signature"]:
                thinking_block["signature"] = self.current_thinking["signature"]
            blocks.append(thinking_block)
            
        if self.current_redacted:
            blocks.append(self.current_redacted)
        return blocks
    
    def get_api_blocks(self):
        """
        Get thinking blocks formatted correctly for the Bedrock API.
        This follows the proper structure required by the API.
        
        Returns:
            list: List of thinking blocks in the format expected by Claude API
        """
        blocks = []
        
        # Add thinking block with proper API structure
        if self.current_thinking["text"]:
            reasoning_block = {
                "reasoningContent": {
                    "reasoningText": {
                        "text": self.current_thinking["text"]
                    }
                }
            }
            
            # Add signature if available - this is required by the API
            if self.current_thinking["signature"]:
                reasoning_block["reasoningContent"]["reasoningText"]["signature"] = self.current_thinking["signature"]
            else:
                # If we don't have a signature, log a warning as this will cause API errors
                logger.warning("Missing signature for thinking block - this will cause API errors")
            
            blocks.append(reasoning_block)
        
        # Add redacted thinking block with proper API structure
        if self.current_redacted and "data" in self.current_redacted:
            blocks.append({
                "redactedReasoningContent": {
                    "data": self.current_redacted["data"]
                }
            })
        
        return blocks
    
    def has_thinking(self):
        """
        Check if there are any thinking blocks.
        
        Returns:
            bool: True if there are thinking blocks, False otherwise
        """
        return bool(self.current_thinking["text"] or self.current_redacted)


def format_message_content(text_content, thinking_blocks=None):
    """
    Format message content with thinking blocks.
    
    Args:
        text_content (str): The text content
        thinking_blocks (list, optional): List of thinking blocks
        
    Returns:
        list: Formatted content list
    """
    content = [{"text": text_content}]
    if thinking_blocks:
        content.extend(thinking_blocks)
    return content