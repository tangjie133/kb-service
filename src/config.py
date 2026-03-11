#!/usr/bin/env python3
"""Configuration for KB Service"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # GitHub 配置
    GITHUB_REPO: str = "tangjie133/knowledge-base"
    GITHUB_TOKEN: Optional[str] = None
    SYNC_INTERVAL: int = 300  # 5分钟同步一次
    
    # Ollama 配置
    OLLAMA_HOST: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    LLM_MODEL: str = "qwen2.5"
    
    # 向量数据库配置
    VECTOR_DB_PATH: str = "./data/vector_db"
    COLLECTION_NAME: str = "knowledge"
    
    # 文本分割配置
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # 检索配置
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
