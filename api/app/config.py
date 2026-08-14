"""Application settings, loaded from the environment with sane local defaults."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = API_ROOT.parent

# The trained models and reference datasets still live with the Streamlit
# prototype. They are data, not code, so they are read in place rather than
# duplicated into this package.
MODELS_DIR = REPO_ROOT / "mdps-streamlit" / "models"
DATASETS_DIR = REPO_ROOT / "mdps-streamlit" / "datasets"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=API_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = f"sqlite:///{API_ROOT / 'mdps.db'}"

    # Auth. The default secret is deliberately obvious so that a production
    # deployment that forgets to set one fails the validator below.
    jwt_secret: str = "dev-only-insecure-secret-change-me"  # noqa: S105 — see validator below
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # Optional. Absent key degrades every AI path to the deterministic
    # rule-based engine rather than erroring.
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:8100", "http://127.0.0.1:8100",
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:8501", "http://127.0.0.1:8501",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "*"
    ])

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @field_validator("jwt_secret")
    @classmethod
    def _reject_default_secret_in_production(cls, value: str, info: ValidationInfo) -> str:
        env = str(info.data.get("environment", "development")).lower()
        if env in {"production", "prod"} and value.startswith("dev-only"):
            raise ValueError("JWT_SECRET must be set to a real secret in production")
        return value

    @property
    def has_groq(self) -> bool:
        key = (self.groq_api_key or "").strip()
        # The prototype shipped this literal placeholder in .env.example.
        return bool(key) and key not in {"YOUR_GROQ_API_KEY_HERE", "GROQ_API_KEY_HERE"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
