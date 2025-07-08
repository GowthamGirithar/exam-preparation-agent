from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_provider(provider_name:str, model_name:str ) :
        if provider_name == "openai":
            # TODO: use it when we shift to the different model for embedding data
            return OpenAIEmbeddings()
        elif provider_name == "sentence_transformers":
            return HuggingFaceEmbeddings(model_name=model_name)
        else:
            raise ValueError(f"Embedding Provider {provider_name} not supported")
