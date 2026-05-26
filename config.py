import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    GROQ_API_KEY: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Railway даёт postgresql://, asyncpg требует postgresql+asyncpg://
        return v.replace("postgresql://", "postgresql+asyncpg://", 1)

    @field_validator("GROQ_API_KEY", mode="before")
    @classmethod
    def fix_groq_api_key(cls, v: str | None) -> str | None:
        # Accept either GROQ_API_KEY or XAI_API_KEY from environment
        return v or os.getenv("XAI_API_KEY")


settings = Settings()
