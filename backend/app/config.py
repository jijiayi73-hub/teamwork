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


settings = Settings()
