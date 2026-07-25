from pathlib import Path

from pydantic import field_validator
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
    # libpq sslmode → asyncpg ssl
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

    # Default TTS / cast provider: "elevenlabs" | "sarvam"
    # Per-request override via CastScript.voice_provider / audiobook preview body.
    tts_provider: str = "elevenlabs"

    # Gemini — visual director (text) + Nano Banana image generation.
    gemini_api_key: str | None = None
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-3.1-flash-image"
    gemini_image_fallback_model: str = "gemini-2.5-flash-image"
    # Image provider for lookbook + scene stills: "openai" | "gemini"
    image_provider: str = "openai"
    openai_image_model: str = "gpt-image-1"
    openai_image_fallback_model: str = "gpt-image-1-mini"
    openai_image_quality: str = "medium"  # low | medium | high (burn credits carefully)
    # Vertical mobile canvas (Pocket FM / Kuku TV style)
    visual_video_width: int = 1080
    visual_video_height: int = 1920
    visual_video_fps: int = 30

    # Databricks workspace + AI Search / Vector Search.
    databricks_host: str | None = None
    databricks_token: str | None = None
    # Team project-context Direct Access index
    databricks_ai_search_endpoint: str | None = None
    databricks_ai_search_index: str | None = None
    # Cast / SFX Delta Sync index
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
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    tavily_api_key: str = ""

    allowed_origins: list[str] = ["*"]

    @property
    def databricks_cast_table_fqn(self) -> str:
        return f"{self.databricks_catalog}.{self.databricks_schema}.{self.databricks_cast_table}"

    @property
    def databricks_cast_index_fqn(self) -> str:
        configured = (self.databricks_vector_search_index or "").strip()
        if configured:
            return configured
        return f"{self.databricks_catalog}.{self.databricks_schema}.{self.databricks_cast_table}_index"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value


settings = Settings()
# Allow OPENAI_API_KEY to stand in for LLM_API_KEY when only one is set.
if not (settings.llm_api_key or "").strip() and (settings.openai_api_key or "").strip():
    settings.llm_api_key = settings.openai_api_key
