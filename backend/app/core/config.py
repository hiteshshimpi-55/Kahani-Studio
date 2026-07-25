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

    # ElevenLabs (TTS). Never commit real keys.
    elevenlabs_api_key: str | None = None
    elevenlabs_default_model_id: str = "eleven_v3"
    elevenlabs_default_output_format: str = "mp3_44100_128"
    elevenlabs_default_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"  # George (library)

    # Sarvam AI (native Hindi TTS via Bulbul v3). Never commit real keys.
    sarvam_api_key: str | None = None
    sarvam_default_speaker: str = "shubh"

    # Default TTS / cast provider: "sarvam" | "elevenlabs"
    # Per-request override via CastScript.voice_provider / audiobook preview body.
    tts_provider: str = "elevenlabs"

    # Replicate (identity sheets + scene stills). Never commit real tokens.
    replicate_api_token: str | None = None
    replicate_face_model: str = "black-forest-labs/flux-schnell"
    # Pin version — owner/name alone can 404 on predictions.create for some accounts.
    replicate_pulid_model: str = (
        "bytedance/flux-pulid:8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b"
    )
    replicate_default_width: int = 576
    replicate_default_height: int = 1024

    # Databricks workspace + AI Search / Vector Search.
    databricks_host: str | None = None
    databricks_token: str | None = None
    # Team project-context Direct Access index
    databricks_ai_search_endpoint: str | None = None
    databricks_ai_search_index: str | None = None
    # Cast / SFX / shot-template Delta Sync index
    databricks_vector_search_endpoint: str | None = None
    databricks_vector_search_index: str | None = None
    databricks_vector_search_columns: str = (
        "id,asset_type,provider,provider_id,name,language,gender,description,"
        "preview_url,free_users_allowed,tags"
    )
    databricks_catalog: str = "workspace"
    databricks_schema: str = "kissa"
    databricks_cast_table: str = "cast_assets"
    databricks_embedding_endpoint: str = "databricks-qwen3-embedding-0-6b"
    databricks_sql_warehouse_id: str | None = None

    # Script Writer LLM (falls back to stub screenplay if LLM_API_KEY unset)
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    # Legacy aliases used by some team snippets
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
    tavily_api_key: str = ""

    allowed_origins: list[str] = ["*"]


    @property
    def databricks_cast_index_fqn(self) -> str:
        configured = (self.databricks_vector_search_index or "").strip()
        if configured:
            return configured
        return f"{self.databricks_catalog}.{self.databricks_schema}.{self.databricks_cast_table}_index"
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
# Allow OPENAI_API_KEY to stand in for LLM_API_KEY when only one is set.
if not (settings.llm_api_key or "").strip() and (settings.openai_api_key or "").strip():
    settings.llm_api_key = settings.openai_api_key

settings = Settings()
