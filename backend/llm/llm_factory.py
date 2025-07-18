from langchain_ollama import OllamaLLM, ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models.llms import BaseLLM
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Union
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_llm(provider: str, model: str, baseURL: str, api_key: str = None) -> Union[BaseLLM, BaseChatModel]:
    """
    Create LLM instance based on provider.
    
    Args:
        provider: LLM provider ("ollama" or "openai")
        model: Model name
        baseURL: Base URL for the provider
        api_key: API key (for OpenAI)
    
    Returns:
        LLM instance
    """
    logger.info(f"Creating LLM: provider={provider}, model={model}")
    
    if provider == "ollama":
        # Ollama doesn't need API keys, uses local models
        logger.info(f"Using Ollama LLM with base URL: {baseURL}")
        return OllamaLLM(model=model, base_url=baseURL, temperature=0)
    
    elif provider == "openai":
        # OpenAI ChatGPT models - requires API key
        if not api_key:
            from config import Config
            api_key = Config.LLM_PROVIDER_API_KEY
        
        if not api_key:
            raise ValueError(
                "API key required for OpenAI. Set LLM_PROVIDER_API_KEY environment variable"
            )
        
        logger.info(f"Using OpenAI ChatGPT model: {model}")
        return ChatOpenAI(
            model=model,
            temperature=0,
            api_key=api_key,
            max_tokens=4000  # Set reasonable default for OpenAI
        )
    
    else:
        raise ValueError(f"Provider '{provider}' not supported. Supported providers: ollama, openai")
