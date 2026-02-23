"""
LLM API Configuration

This module provides configuration for the LLM API wrapper.
LLM is an unofficial OpenAI-compatible API that uses the same interface.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class LLMConfig:
    """Configuration for LLM API"""
    
    # API Base URLs
    BASE_URL = os.getenv("LLM_BASE_URL")
    
    # Specific endpoints
    CHAT_COMPLETIONS_URL = f"{BASE_URL}/chat/completions"
    IMAGE_GENERATIONS_URL = f"{BASE_URL}/images/generations"
    
    # API Key - can use same env var as OpenAI or separate one
    API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    # Model mappings (if LLM uses different model names)
    # Currently assuming same names as OpenAI
    MODEL_MAPPINGS = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini", 
        "gpt-4": "gpt-4",
        "dall-e-3": "dall-e-3",
    }
    
    # Timeouts
    DEFAULT_TIMEOUT = 120.0
    IMAGE_GEN_TIMEOUT = 180.0
    
    # Logging
    VERBOSE = os.getenv("LLM_VERBOSE", "false").lower() == "true"
    
    @classmethod
    def get_model_name(cls, openai_model: str) -> str:
        """Get the LLM model name for an OpenAI model"""
        return cls.MODEL_MAPPINGS.get(openai_model, openai_model)
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.API_KEY:
            raise ValueError(
                "API key not found. Please set LLM_API_KEY or OPENAI_API_KEY "
                "environment variable."
            )
        return True


llm_config = LLMConfig()
