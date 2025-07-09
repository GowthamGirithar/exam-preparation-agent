from retrievers.vector_store_factory import get_vector_store
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_community.tools.google_serper.tool import GoogleSerperAPIWrapper
from config import Config


class SearchInput(BaseModel):
    query: str = Field(description="query to search for English grammar, vocabulary, comprehension passages, and language skills for CLAT exam")
    max_results: int = Field(default=5, description="maximum number of results to return")


@tool("english_search_document", args_schema=SearchInput)
# description of method with args is important for agent to understand this tool
def english_document_search(query: str, max_results: int = 5):
       """Search English language study materials for CLAT exam preparation.
       
       Use this tool ONLY for:
       - English grammar questions (tenses, parts of speech, sentence structure)
       - Vocabulary and word meanings
       - Reading comprehension passages and techniques
       - English language skills and rules
       
       DO NOT use for current events, general knowledge, or factual questions about people/places.
    
    Args:
        query: English language topic to search for (grammar, vocabulary, comprehension)
        max_results: the number of similar documents to return (default: 5)
    """

       try:
            vector_store = get_vector_store(provider_name=Config.VECTOR_STORE_PROVIDER,
                                                 embedding_provider=Config.EMBEDDING_PROVIDER,
                                                 embedding_model=Config.DEFAULT_EMBEDDING_MODEL,
                                                 collection_name=Config.ENGLISH_COLLECTION)
            # Pass max_results to the retriever instead of filtering afterwards
            results = vector_store.get_chroma_retriever(top_k=max_results).invoke(query)
            print(f"the length of resources is {len(results)}")
            return results
       except Exception as e:
            return str(e)

@tool("search_web")
def search_web(query: str) -> str:
    """Search the web for current information, facts, news, and general knowledge.
    
    Use this tool for:
    - Current events and news
    - Factual questions about people, places, organizations
    - General knowledge questions
    - Information not related to English language skills
    
    Input should be a search query string."""
    try:
        # Configure serper to get more focused results
        Config.validate()  # Ensure API key is available
        serper = GoogleSerperAPIWrapper(
            serper_api_key=Config.GOOGLE_SERPER_API_KEY,
            k=Config.SEARCH_RESULTS_LIMIT,  # Use config value
        )
        
        # Get the parsed response (this uses _parse_snippets internally)
        # serper.results(query) to see full response
        response = serper.run(query)
        print("Serper response:", response)
        print("\n")
        return response
        
    except Exception as e:
        return f"Error searching web: {str(e)}"

# Modern tools for new agent (using @tool decorator)
TOOLS_AVAILABLE = {
      "english_search_document": english_document_search,
      "search_web": search_web
}

def get_registered_tools(tools_names: list[str]) -> list:
        """Get tools - returns modern @tool functions for new agent"""
        registered_tools = []
        for name in tools_names:
                if name in TOOLS_AVAILABLE:
                        registered_tools.append(TOOLS_AVAILABLE[name])
        return registered_tools
