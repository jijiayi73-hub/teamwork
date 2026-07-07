from dataclasses import dataclass
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


settings = Settings()
