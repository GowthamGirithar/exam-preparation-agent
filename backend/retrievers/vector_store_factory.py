from retrievers import ChromaRetriever


def get_vector_store(provider_name: str, embedding_provider: str, embedding_model: str, collection_name: str = "default") :
    if provider_name == "chroma":
        return ChromaRetriever(embedding_provider, embedding_model, collection_name)
    else:
        raise ValueError(f"Vector Store Provider {provider_name} not supported")
