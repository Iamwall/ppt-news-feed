"""Application configuration using pydantic-settings."""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "Scientific News Digest"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Database (default to SQLite for easy testing)
    database_url: str = "sqlite+aiosqlite:///./science_digest.db"
    database_echo: bool = False
    
    # Demo mode (works without external APIs)
    demo_mode: bool = True
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # AI Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    google_api_key: str = ""
    groq_api_key: str = ""
    
    # Default AI settings
    default_ai_provider: Literal["openai", "anthropic", "ollama", "gemini", "groq"] = "gemini"
    default_ai_model: str = "gemini-2.0-flash-exp"
    default_image_provider: Literal["dalle", "gemini", "stable_diffusion"] = "gemini"
    
    # Email
    sendgrid_api_key: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "digest@sciencenews.local"
    
    # External APIs
    semantic_scholar_api_key: str = ""
    
    # File storage
    upload_dir: str = "./uploads"
    generated_images_dir: str = "./generated_images"
    
    # Rate limiting
    pubmed_requests_per_second: float = 3.0
    arxiv_requests_per_second: float = 1.0
    semantic_scholar_requests_per_second: float = 10.0


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
