"""
Application settings and configuration
"""
import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings loaded from environment"""
    
    # Flask
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # API
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '5000'))
    
    # Frontend
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    
    # AI/LLM
    GROQ_API_KEY: Optional[str] = os.getenv('GROQ_API_KEY')
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    
    # LangChain
    LANGCHAIN_API_KEY: Optional[str] = os.getenv('LANGCHAIN_API_KEY')
    LANGCHAIN_TRACING_V2: bool = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    LANGCHAIN_ENDPOINT: str = os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
    LANGCHAIN_PROJECT: str = os.getenv('LANGCHAIN_PROJECT', 'Vishleshak_AI')
    
    # File Storage
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'data/uploads')
    MAX_CONTENT_LENGTH: int = int(os.getenv('MAX_CONTENT_LENGTH', str(50 * 1024 * 1024)))  # 50MB
    
    # Vector Store
    VECTOR_STORE_PATH: str = os.getenv('VECTOR_STORE_PATH', 'storage/vector_db')
    
    @property
    def is_production(self) -> bool:
        return not self.DEBUG


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
