from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    GROQ_API_KEY: str
    ADMIN_TG_ID: int
    SENTRY_DSN: str = ""
    ENV: str = "production"
    STICKER_SET_NAME: str = "catsunicmass"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Railway даёт postgresql://, asyncpg требует postgresql+asyncpg://
        return v.replace("postgresql://", "postgresql+asyncpg://", 1)


settings = Settings()
