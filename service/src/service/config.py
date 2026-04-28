"""Runtime configuration for the service.

All settings are loaded from environment variables (or a .env file discovered by
pydantic-settings). Missing required values cause startup to fail — see
`require_runtime_ready` — rather than silently defaulting to unsafe behavior.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvName = Literal["dev", "staging", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


def _default_data_json() -> Path:
    """Default location of data.json, resolved once at import."""
    # service/src/service/config.py -> service/ -> repo root
    return Path(__file__).resolve().parents[3] / "data.json"


def _default_env_file() -> Path:
    """Resolve .env from the repo root (service/src/service/ -> repo root)."""
    return Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_default_env_file()),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    anthropic_api_key: SecretStr | None = None
    env: EnvName = "dev"
    log_level: LogLevel = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    data_json_path: Path = Field(default_factory=_default_data_json)

    @field_validator("data_json_path", mode="before")
    @classmethod
    def _coerce_empty_data_json_path(cls, v: object) -> object:
        """Treat an empty DATA_JSON_PATH as unset, falling back to the default."""
        if isinstance(v, str) and not v.strip():
            return _default_data_json()
        return v

    predictions_rate_limit_per_minute: int = 10
    llm_monthly_spend_cap_usd: float = 50.0
    calibration_stale_after_days: int = 14

    sync_interval_minutes: int = 60
    lotofacil_api_url: str = (
        "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
    )


class ConfigError(RuntimeError):
    """Raised when startup-time configuration is missing or invalid."""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide Settings singleton."""
    return Settings()


def reset_settings_cache() -> None:
    """Drop the cached Settings singleton. Only used in tests."""
    get_settings.cache_clear()


def require_runtime_ready(settings: Settings | None = None) -> Settings:
    """Validate hard runtime preconditions; raise ConfigError if unmet.

    Specifically: refuse to start without ANTHROPIC_API_KEY set, per the
    prediction-service-api spec. Call this from the FastAPI startup hook.
    """
    s = settings or get_settings()
    if s.anthropic_api_key is None or not s.anthropic_api_key.get_secret_value():
        raise ConfigError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and provide a key; "
            "the service refuses to start without one."
        )
    if not s.data_json_path.is_file():
        raise ConfigError(
            f"data.json not found at {s.data_json_path}. "
            "Set DATA_JSON_PATH or place the dataset at the default location."
        )
    return s
