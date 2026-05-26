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
    def force_asyncpg_dialect(cls, v: str) -> str:
        """Rewrite postgresql:// → postgresql+asyncpg:// so SQLAlchemy's
        async engine works regardless of how the env var is set."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
