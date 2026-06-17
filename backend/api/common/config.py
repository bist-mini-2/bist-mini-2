import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Bist Mini 2 API"
    ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # API Configuration
    API_V1_STR: str = "/api/v1"

    # JWT Settings
    JWT_SECRET_KEY: str = "com.mycompany.backendapi.secret.key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60  # 24 hours (1440 minutes)

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@kosa165.iptime.org:50003/postgres"

    # OpenAI API Key Configuration
    OPENAI_API_KEY: str = ""

    # Automatically load from .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def PGVECTOR_URL(self) -> str:
        """PGVector(psycopg_async) 연결 문자열 — DATABASE_URL에서 드라이버만 교체"""
        return self.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql+psycopg_async://"
        )


# Instantiate settings to be imported elsewhere
settings = Settings()

