"""
ELK Kernel - Pydantic Settings Configuration
Best practice configuration management with:
- Environment variable loading
- Nested model support
- Secrets handling (SecretStr)
- Validation on load
"""

import os
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):
    """LLM provider configuration."""
    provider: str = "gemini"
    
    # Cloud settings
    cloud_model: str = "gemini-1.5-flash"
    cloud_api_key: Optional[SecretStr] = None
    
    # Local settings
    local_model: str = "llama3"
    local_base_url: str = "http://localhost:11434"
    
    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0
    timeout_seconds: int = 60


class ASRSettings(BaseModel):
    """Whisper ASR configuration."""
    model: str = "whisper-kabyle-dgpc-v6-ct2"
    device: str = "auto"
    compute_type: str = "int8_float16"
    enable_alignment: bool = True
    batch_size: int = 16


class RAGSettings(BaseModel):
    """RAG/Vector store configuration."""
    enable_vector: bool = True
    collection_name: str = "elk_knowledge"
    persist_directory: str = "./chromadb"
    
    # Hybrid weights
    keyword_weight: float = 0.5
    vector_weight: float = 0.5
    
    # Reranking
    enable_reranking: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    min_score_threshold: float = 0.3
    top_k: int = 10


class ConfidenceSettings(BaseModel):
    """Confidence calculator configuration."""
    asr_weight: float = 0.40
    entity_weight: float = 0.35
    rag_weight: float = 0.25
    human_review_threshold: float = 0.70


class LoggingSettings(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "jsonl"
    log_dir: str = "logs"
    enable_audit_trail: bool = True


class ServerSettings(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False


class ELKSettings(BaseSettings):
    """
    Main ELK configuration.
    
    Load from environment variables with ELK_ prefix:
        ELK_LLM__PROVIDER=ollama
        ELK_ASR__MODEL=whisper-large-v3
    
    Or from .env file.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="ELK_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Pack configuration
    pack_name: str = "dz-kab-protection"
    pack_version: str = "1.0.0"
    
    # Nested settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    asr: ASRSettings = Field(default_factory=ASRSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    confidence: ConfidenceSettings = Field(default_factory=ConfidenceSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    
    def get_llm_api_key(self) -> Optional[str]:
        """Get API key as string (for use with clients)."""
        if self.llm.cloud_api_key:
            return self.llm.cloud_api_key.get_secret_value()
        # Fallback to direct env var
        return os.getenv("GEMINI_API_KEY")


# Global settings instance (singleton pattern)
_settings: Optional[ELKSettings] = None


def get_settings() -> ELKSettings:
    """
    Get or create settings instance.
    Use this function for dependency injection in FastAPI.
    """
    global _settings
    if _settings is None:
        _settings = ELKSettings()
    return _settings


def reload_settings() -> ELKSettings:
    """Force reload settings (useful after env changes)."""
    global _settings
    _settings = ELKSettings()
    return _settings
