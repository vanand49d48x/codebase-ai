import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Workspace Configuration
    workspace_dir: str = "/app/workspace"
    
    # LLM Configuration
    llm_provider: str = "ollama"
    llm_model: str = "codellama-q"
    ollama_host: str = "http://ollama:11434"
    
    # Embedding Configuration
    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Qdrant Configuration
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "code_chunks"
    
    # Database Configuration
    db_url: str = "postgresql://user:password@postgres:5432/codebase_db"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'
        extra = 'ignore'


# Global settings instance
settings = Settings()
