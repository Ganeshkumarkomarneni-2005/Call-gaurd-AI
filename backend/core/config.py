"""Application configuration via Pydantic BaseSettings."""
from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------ App --
    app_name: str = "CallGuard AI"
    version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # -------------------------------------------------------------- Database --
    database_url: str = "postgresql://callguard:callguard@localhost:5432/callguard"

    # ------------------------------------------------------------ Telephony --
    telephony_provider: str = "mock"
    exotel_sid: str = ""
    exotel_token: str = ""
    exotel_from_number: str = ""
    exotel_subdomain: str = ""

    # ------------------------------------------------------------------ STT --
    stt_provider: str = "mock"
    google_speech_api_key: str = ""
    deepgram_api_key: str = ""

    # ------------------------------------------------------------------ TTS --
    tts_provider: str = "mock"
    google_tts_api_key: str = ""
    elevenlabs_api_key: str = ""

    # ------------------------------------------------------------------ LLM --
    llm_provider: str = "mock"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    # ---------------------------------------------------------------- CORS --
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # --------------------------------------------------------- Notification --
    notification_provider: str = "web_push"


def get_settings() -> Settings:
    """Return a new Settings instance (reads .env on every call)."""
    return Settings()


# Module-level singleton -- import this throughout the app.
settings: Settings = get_settings()
