from langchain_ollama import OllamaLLM
from langchain_core.language_models.llms import BaseLLM



def get_llm(provider: str , model: str , baseURL: str) -> BaseLLM:
    if provider == "ollama":
        # no max_token in ollama, alternative be num_predict
        return OllamaLLM(model=model, base_url=baseURL, temperature=0)
    else:
        raise ValueError(f"Provider {provider} not supported")
    
