# Old style tools for legacy agent compatibility
from langchain.tools import Tool
from retrievers.vector_store_factory import get_vector_store
from config import Config



TOOLS = {
    "english_search_document": Tool(
        name="english_search_document",
        description="Search the given query using vector similarity search anything related to english exam questions",
        func=lambda x : get_vector_store(provider_name=Config.VECTOR_STORE_PROVIDER,
                                                 embedding_provider=Config.EMBEDDING_PROVIDER,
                                                 embedding_model=Config.DEFAULT_EMBEDDING_MODEL,
                                                 collection_name=Config.ENGLISH_COLLECTION).get_chroma_retriever().invoke(x),
    ),
}


def get_legacy_tools(tools_names: list[str]) -> list:
        """Get legacy Tool objects for old agent"""
        registered_tools = []
        for name in tools_names:
                if name in TOOLS:
                        registered_tools.append(TOOLS[name])
        return registered_tools
