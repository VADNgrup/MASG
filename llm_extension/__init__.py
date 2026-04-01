"""
LLM Extension - Auto-patching Module

This module automatically patches OpenAI and LangChain imports to use LLM API.

Usage:
    # At the very beginning of your main script or entry point:
    import llm_extension
    
    # Now all OpenAI API calls will use LLM automatically!
    from openai import OpenAI  # This will actually be LLMClient
    from langchain_openai import ChatOpenAI  # This will actually be ChatLLM
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our wrappers
from .llm_client import LLMClient
from .llm_langchain import ChatLLM
from .llm_config import llm_config


def patch_openai():
    """Patch openai module to use LLMClient"""
    try:
        import openai
        
        # Store original for reference
        if not hasattr(openai, '_original_OpenAI'):
            openai._original_OpenAI = openai.OpenAI
        
        # Replace with LLM wrapper
        openai.OpenAI = LLMClient
        
        logger.info("✅ Successfully patched openai.OpenAI → LLMClient")
        return True
    except ImportError:
        logger.warning("⚠️  openai module not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to patch openai module: {e}")
        return False


def patch_langchain():
    """Patch langchain_openai module to use ChatLLM"""
    try:
        import langchain_openai
        
        # Store original for reference
        if not hasattr(langchain_openai, '_original_ChatOpenAI'):
            langchain_openai._original_ChatOpenAI = langchain_openai.ChatOpenAI
        
        # Replace with LLM wrapper
        langchain_openai.ChatOpenAI = ChatLLM
        
        logger.info("✅ Successfully patched langchain_openai.ChatOpenAI → ChatLLM")
        return True
    except ImportError:
        logger.warning("⚠️  langchain_openai module not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to patch langchain_openai module: {e}")
        return False


def unpatch_all():
    """Restore original OpenAI modules (for debugging/testing)"""
    try:
        import openai
        if hasattr(openai, '_original_OpenAI'):
            openai.OpenAI = openai._original_OpenAI
            logger.info("Restored original openai.OpenAI")
    except:
        pass
    
    try:
        import langchain_openai
        if hasattr(langchain_openai, '_original_ChatOpenAI'):
            langchain_openai.ChatOpenAI = langchain_openai._original_ChatOpenAI
            logger.info("Restored original langchain_openai.ChatOpenAI")
    except:
        pass


def apply_patches(verbose: bool = True):
    """
    Apply all patches to use LLM API.
    
    Args:
        verbose: Whether to print patch status
    
    Returns:
        dict: Status of each patch
    """
    if not verbose:
        logger.setLevel(logging.WARNING)
    
    # Validate config
    try:
        llm_config.validate()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        return {"error": str(e)}
    
    results = {
        "openai": patch_openai(),
        "langchain": patch_langchain(),
        "config": {
            "base_url": llm_config.BASE_URL,
            "api_key_set": bool(llm_config.API_KEY)
        }
    }
    
    if verbose and all([results["openai"], results["langchain"]]):
        logger.info("🚀 LLM extension activated! All OpenAI calls will use LLM API.")
    
    return results


# Auto-apply patches when module is imported
if __name__ != "__main__":
    logger.info("=" * 60)
    logger.info("General LLM Wrapper Initializing")
    logger.info("=" * 60)
    apply_patches(verbose=llm_config.VERBOSE)


# Export main classes for direct import
__all__ = [
    'LLMClient',
    'ChatLLM',
    'llm_config',
    'apply_patches',
    'unpatch_all'
]
