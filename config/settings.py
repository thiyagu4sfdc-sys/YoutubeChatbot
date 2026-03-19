"""Configuration settings for Video RAG application."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    print(f"Settings key: {openai_api_key}")
    openai_model: str = "gpt-4.1-mini-2025-04-14"  # Primary model for answers
    openai_model_verification: str = "gpt-3.5-turbo"  # Model for verification
    embedding_model: str = "text-embedding-3-small"
    
    # RAG Configuration
    chunk_size: int = 1000  # Characters per chunk
    chunk_overlap: int = 200  # Overlap between chunks
    max_retrieved_chunks: int = 5  # Top-k chunks to retrieve
    confidence_threshold: float = 0.7  # Minimum confidence to return answer
    
    # FAISS Configuration
    faiss_index_path: str = str(Path(__file__).parent.parent / "data" / "faiss_index")
    faiss_metadata_path: str = str(Path(__file__).parent.parent / "data" / "metadata.pkl")
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    
    # Streamlit Configuration
    streamlit_port: int = 8501
    max_history_messages: int = 10
    
    # Processing Configuration
    youtube_timeout: int = 30
    embedding_batch_size: int = 10
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from env file

settings = Settings()
