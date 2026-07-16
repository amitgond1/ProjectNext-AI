from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Project Recommender"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./project_recommender.db"
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    allowed_origins: str = "http://localhost:5174,http://127.0.0.1:5174,http://localhost:5173"
    max_recommendations: int = 25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
