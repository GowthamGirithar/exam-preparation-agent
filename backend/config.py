import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Configuration
    LLM_HOST = os.getenv("LLM_HOST", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
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
    AGENT_NAME = os.getenv("AGENT_NAME", "DynamicLawAgent")
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
    VERBOSE_MODE = os.getenv("VERBOSE_MODE", "true").lower() == "true"
    SEARCH_RESULTS_LIMIT = int(os.getenv("SEARCH_RESULTS_LIMIT", "3"))
    
    # LangSmith Configuration
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "law-exam-agent-evaluation")
    LANGSMITH_API_URL = os.getenv("LANGSMITH_API_URL", "https://api.smith.langchain.com")
    
    # Evaluation Thresholds
    EVALUATION_THRESHOLDS = {
        "correctness": float(os.getenv("CORRECTNESS_THRESHOLD", "0.75")),
        "tool_selection_accuracy": float(os.getenv("TOOL_SELECTION_THRESHOLD", "0.90")),
        "relevance": float(os.getenv("RELEVANCE_THRESHOLD", "0.80")),
        "completeness": float(os.getenv("COMPLETENESS_THRESHOLD", "0.70")),
        "memory_retention": float(os.getenv("MEMORY_RETENTION_THRESHOLD", "0.85"))
    }

    # Evaluation Local - determine whether to run custom evaluation or using langsmith
    EVALUATION_LOCAL = os.getenv("EVALUATION_LOCAL", "true").strip().lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_SERPER_API_KEY:
            raise ValueError("GOOGLE_SERPER_API_KEY is required")
