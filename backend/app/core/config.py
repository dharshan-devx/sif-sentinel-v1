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
    # Precursor / Aggregate Risk (Phase H)
    aggregate_density_weight: float = 0.30
    aggregate_frequency_weight: float = 0.20
    aggregate_failure_weight: float = 0.20
    aggregate_recency_weight: float = 0.15
    aggregate_trend_weight: float = 0.10
    aggregate_spread_weight: float = 0.05
    
    # Precursor Logic
    precursor_min_occurrences: int = 3
    precursor_lookback_days: int = 90
    
    # Phase I Safety Risk Engine (1-100 Scale)
    risk_engine_version: str = "v1"
    risk_score_min: int = 1
    risk_score_max: int = 100
    risk_critical_threshold: int = 81
    risk_high_threshold: int = 56
    risk_medium_threshold: int = 31
    
    # Phase I Risk Engine Weights
    risk_weight_consequence: int = 30
    risk_weight_control: int = 30
    risk_weight_lsr: int = 15
    risk_weight_precursor: int = 25
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
