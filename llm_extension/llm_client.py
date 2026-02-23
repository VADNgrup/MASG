"""
LLM Client Wrapper

This module provides a wrapper for the OpenAI client that redirects all requests
to the LLM API (unofficial OpenAI-compatible API).

Usage:
    from llm_extension.llm_client import LLMClient
    
    client = LLMClient(api_key="your_key")
    response = client.chat.completions.create(...)
"""

from openai import OpenAI
from typing import Optional
import logging
from .llm_config import llm_config

# Setup logging
logger = logging.getLogger(__name__)


class LLMClient(OpenAI):
    """
    Wrapper for OpenAI client that uses LLM API.
    
    This class inherits from OpenAI and overrides the base_url to point to LLM.
    All other functionality remains the same, ensuring 100% compatibility.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        **kwargs
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: LLM API key (defaults to env LLM_API_KEY or OPENAI_API_KEY)
            base_url: Base URL for API (defaults to LLM URL)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            **kwargs: Additional arguments passed to OpenAI client
        """
        # Use LLM config if not provided
        if api_key is None:
            api_key = llm_config.API_KEY
        
        if base_url is None:
            base_url = llm_config.BASE_URL
        
        if timeout is None:
            timeout = llm_config.DEFAULT_TIMEOUT
        
        # Log initialization
        if llm_config.VERBOSE:
            logger.info(f"Initializing LLMClient with base_url: {base_url}")
        
        # Initialize parent OpenAI class with LLM settings
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs
        )
    
    def __repr__(self):
        return f"LLMClient(base_url='{self.base_url}')"


# Convenience function to create a LLM client
def create_llm_client(api_key: Optional[str] = None, **kwargs) -> LLMClient:
    """
    Create a LLM client instance.
    
    Args:
        api_key: Optional API key
        **kwargs: Additional arguments for LLMClient
    
    Returns:
        LLMClient instance
    """
    return LLMClient(api_key=api_key, **kwargs)
