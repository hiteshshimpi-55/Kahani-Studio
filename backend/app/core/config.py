from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Walk up from this file to find .env at the project root
_HERE = Path(__file__).resolve().parent  # app/core/
_ENV = next(
    (p / ".env" for p in [_HERE, *_HERE.parents] if (p / ".env").exists()),
    _HERE / ".env",
)


def normalize_database_url(url: str) -> str:
    """Accept postgresql://… and map to asyncpg + ssl query params."""
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
    url = url.replace("sslmode=require", "ssl=require")
    url = url.replace("sslmode=verify-full", "ssl=require")
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "kahani"
    api_prefix: str = "/api"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://kissa:kissa@postgres:5432/kissa"
    redis_url: str = "redis://redis:6379/0"
    data_dir: str = "/data"

    allowed_origins: list[str] = ["*"]

    # LLM (Script Writer + chat orchestrator)
    llm_provider: str = "openai"
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"),
    )
    llm_model: str = "gpt-4o"

    # Legacy aliases still used in some paths
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Tavily
    tavily_api_key: str = ""

    # Databricks AI Search (optional — local chunk fallback if unset)
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_ai_search_endpoint: str = ""
    databricks_ai_search_index: str = ""
    databricks_embedding_endpoint: str = ""

    # ElevenLabs TTS (timeline dialogue). Without key, API returns stub tones.
    elevenlabs_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("ELEVENLABS_API_KEY"),
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value

    @property
    def effective_llm_api_key(self) -> str:
        return (self.llm_api_key or self.openai_api_key or "").strip()


settings = Settings()
