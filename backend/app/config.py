from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "kissa"
    api_prefix: str = "/api"
    database_url: str = "postgresql+asyncpg://kissa:kissa@postgres:5432/kissa"
    redis_url: str = "redis://redis:6379/0"
    data_dir: str = "/data"


settings = Settings()
