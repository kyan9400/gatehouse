from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Hosting providers may materialize blank entries from .env.example. Treat
    # those as unset so optional deployment settings fall back to safe defaults.
    model_config = SettingsConfigDict(
        env_prefix="GATEHOUSE_",
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "Gatehouse"
    environment: str = "local"
    database_url: str = "sqlite+aiosqlite:///./gatehouse.db"
    api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:4173"
    demo_seed: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
