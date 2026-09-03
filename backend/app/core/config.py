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
    precursor_recency_lambda: float = 0.03
    risk_density_weight: float = 0.30
    risk_frequency_weight: float = 0.20
    risk_failure_weight: float = 0.20
    risk_recency_weight: float = 0.15
    risk_trend_weight: float = 0.10
    risk_spread_weight: float = 0.05
    precursor_min_occurrences: int = 3
    precursor_lookback_days: int = 90
    risk_critical_threshold: float = 0.75
    risk_high_threshold: float = 0.55
    risk_medium_threshold: float = 0.30
    demo_mode: bool = False
    # Report text validation — minimum is 10 chars to allow short but meaningful
    # safety observations (e.g. "Slip near valve"). Maximum is 20 000 chars to
    # prevent oversized payloads from reaching the tokeniser/classifier.
    report_text_min_length: int = 10
    report_text_max_length: int = 20_000
    # NOTE: max_upload_bytes has been removed. No file-upload endpoint exists in
    # this codebase. If an upload route is added in a future phase, re-introduce
    # this setting and enforce it before reading the full payload into memory.

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
