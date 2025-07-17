from langchain_ollama import OllamaLLM, ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models.llms import BaseLLM
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Union
import os



def get_llm(provider: str , model: str , baseURL: str, api_key: str = None) -> Union[BaseLLM, BaseChatModel]:
    if provider == "ollama":
        # no max_token in ollama, alternative be num_predict
        return OllamaLLM(model=model, base_url=baseURL, temperature=0)
    elif provider == "openai":
        # OpenAI ChatGPT models - generic API key support
        if not api_key:
            api_key = os.getenv("LLM_PROVIDER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key required for OpenAI. Set LLM_PROVIDER_API_KEY environment variable")
        return ChatOpenAI(
            model=model,
            temperature=0,
            api_key=api_key
        )
    else:
        raise ValueError(f"Provider {provider} not supported. Supported: ollama, openai")
