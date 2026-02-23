"""
LLM LangChain Wrapper

This module provides a wrapper for langchain_openai.ChatOpenAI that uses LLM API.

Usage:
    from llm_extension.llm_langchain import ChatLLM
    
    llm = ChatLLM(model="gpt-4o", temperature=0.3)
    response = llm.invoke("Hello!")
"""

from langchain_openai import ChatOpenAI
from typing import Optional, Any, Dict
import logging
from .llm_config import llm_config

# Setup logging
logger = logging.getLogger(__name__)


class ChatLLM(ChatOpenAI):
    """
    Wrapper for LangChain's ChatOpenAI that uses LLM API.
    
    This class inherits from ChatOpenAI and overrides the API base URL
    to point to LLM while maintaining full LangChain compatibility.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Initialize ChatLLM.
        
        Args:
            model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            api_key: LLM API key (defaults to env var)
            base_url: Base URL for API (defaults to LLM URL)
            **kwargs: Additional arguments passed to ChatOpenAI
        """
        # Use LLM config if not provided
        if api_key is None:
            api_key = llm_config.API_KEY
        
        if base_url is None:
            base_url = llm_config.BASE_URL
        
        if timeout is None:
            timeout = llm_config.DEFAULT_TIMEOUT
        
        # Map model name if needed
        llm_model = llm_config.get_model_name(model)
        
        # Log initialization
        if llm_config.VERBOSE:
            logger.info(
                f"Initializing ChatLLM with model={llm_model}, "
                f"base_url={base_url}"
            )
        
        # Initialize parent ChatOpenAI class with LLM settings
        super().__init__(
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            openai_api_key=api_key,
            openai_api_base=base_url,
            **kwargs
        )
    
    def __repr__(self):
        return (
            f"ChatLLM(model='{self.model_name}', "
            f"temperature={self.temperature})"
        )


# Convenience function to create a ChatLLM instance
def create_chat_llm(
    model: str = "gpt-4o",
    temperature: float = 0.7,
    **kwargs
) -> ChatLLM:
    """
    Create a ChatLLM instance.
    
    Args:
        model: Model name
        temperature: Sampling temperature
        **kwargs: Additional arguments for ChatLLM
    
    Returns:
        ChatLLM instance
    """
    return ChatLLM(model=model, temperature=temperature, **kwargs)
