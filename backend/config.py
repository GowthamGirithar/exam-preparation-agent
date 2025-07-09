import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    
    # API Keys
    GOOGLE_SERPER_API_KEY = os.getenv("GOOGLE_SERPER_API_KEY")
    
    # Vector Store Configuration
    VECTOR_STORE_PROVIDER = os.getenv("VECTOR_STORE_PROVIDER", "chroma")
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
    DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Collection Names
    ENGLISH_COLLECTION = os.getenv("ENGLISH_COLLECTION", "english")
    MICROSERVICE_COLLECTION = os.getenv("MICROSERVICE_COLLECTION", "microservices")
    LAW_COLLECTION = os.getenv("LAW_COLLECTION", "law")
    
    # Agent Configuration
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
    VERBOSE_MODE = os.getenv("VERBOSE_MODE", "true").lower() == "true"
    SEARCH_RESULTS_LIMIT = int(os.getenv("SEARCH_RESULTS_LIMIT", "3"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_SERPER_API_KEY:
            raise ValueError("GOOGLE_SERPER_API_KEY is required")
