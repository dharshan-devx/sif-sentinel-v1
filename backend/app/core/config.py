from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    analysis_review_threshold: float = 0.62
    classifier_weight: float = 0.45
    entity_weight: float = 0.25
    rule_weight: float = 0.20
    evidence_weight: float = 0.10

    @field_validator("jwt_secret_key")
    @classmethod
    def nonempty_secret(cls, value: str) -> str:
        if len(value) < 16:
            raise ValueError("JWT_SECRET_KEY must contain at least 16 characters")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins from the documented comma-separated environment value."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
