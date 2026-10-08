import os
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """TrustLens configuration settings."""
    app_name: str = "TrustLens AIML Engine"
    app_version: str = "1.0.0-phase4"
    debug: bool = False

    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    tavily_api_key: Optional[str] = None
    search_provider: str = "duckduckgo"

    # Phase 5 Multimodal AI Settings
    llm_provider: str = "groq"
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    multimodal_model: str = "qwen/qwen3.8-27b"
    multimodal_timeout_seconds: float = 35.0

    rate_limit_per_minute: int = 15
    max_upload_size_bytes: int = 30 * 1024 * 1024  # 30 MB
    max_image_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB (Phase 4)


    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
