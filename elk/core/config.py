import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Emergency Lang Kit (ELK)"
    VERSION: str = "0.2.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Infrastructure
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./elk_jobs.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    QUEUE_OP_TIMEOUT: float = float(os.getenv("QUEUE_OP_TIMEOUT", "2.0"))
    MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", "500"))

    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/elk/uploads")
    MAX_AUDIO_SIZE_MB: int = int(os.getenv("MAX_AUDIO_SIZE_MB", "10"))
    UPLOAD_TTL_SECONDS: int = int(os.getenv("UPLOAD_TTL_SECONDS", "86400"))

    # Worker Performance
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
    CONNECTOR_TIMEOUT: float = float(os.getenv("CONNECTOR_TIMEOUT", "5.0"))
    CONNECTOR_MAX_RETRIES: int = int(os.getenv("CONNECTOR_MAX_RETRIES", "3"))
    CONNECTOR_RETRY_BASE_DELAY: float = float(os.getenv("CONNECTOR_RETRY_BASE_DELAY", "0.5"))

    # Connectors
    CONNECTOR_TYPE: str = os.getenv("CONNECTOR_TYPE", "mock") # or "webhook"
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    # API Security
    API_KEY: str | None = os.getenv("API_KEY")
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost,http://127.0.0.1"
    ).split(",")
    ALLOWED_HOSTS: list[str] = os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,testserver"
    ).split(",")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
