from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_env: str = getenv("APP_ENV", "development")
    database_url: str = getenv("DATABASE_URL", "sqlite:///./data/app.db")
    secret_key: str = getenv("SECRET_KEY", "innergarden-local-development-secret-key")


settings = Settings()
