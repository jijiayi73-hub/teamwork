from dataclasses import dataclass, field
from os import getenv
from typing import Literal


@dataclass(frozen=True)
class Settings:
    app_env: str = getenv("APP_ENV", "development")
    database_url: str = getenv("DATABASE_URL", "sqlite:///./data/app.db")
    secret_key: str = getenv("SECRET_KEY", "innergarden-local-development-secret-key")

    # Logging configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = getenv("LOG_LEVEL", "INFO")
    log_format: Literal["json", "console"] = getenv("LOG_FORMAT", "console")

    # CORS configuration - comma-separated list of allowed origins
    # For production, set via environment variable
    cors_origins: list[str] = field(default_factory=lambda: getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000"
    ).split(","))

    # AI Provider configuration
    ai_provider: Literal["openai", "deepseek"] = getenv("AI_PROVIDER", "openai")
    ai_default_model: str = getenv("AI_DEFAULT_MODEL", "gpt-4o-mini")
    ai_timeout: int = int(getenv("AI_TIMEOUT", "30"))
    deepseek_base_url: str = getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


settings = Settings()
