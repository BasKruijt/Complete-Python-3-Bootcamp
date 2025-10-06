from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # Scheduling / Locale
    RUN_AT: str = Field(default="07:15")
    TZ: str = Field(default="Europe/Amsterdam")

    # Email / Gmail
    GMAIL_USER: Optional[str] = None
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REDIRECT_URI: str = Field(default="http://localhost:8080/")
    GMAIL_TOKEN_PATH: Path = Field(default=Path("config/gmail_token.json"))

    # Microsoft Graph (preferred)
    PROVIDER_CALENDAR: str = Field(default="graph")  # or "google"
    MS_TENANT_ID: Optional[str] = None
    MS_CLIENT_ID: Optional[str] = None
    MS_CLIENT_SECRET: Optional[str] = None
    MS_CACHE_PATH: Path = Field(default=Path("config/msal_cache.json"))

    # Google Calendar (alternative)
    GCAL_TOKEN_PATH: Path = Field(default=Path("config/gcal_token.json"))

    # Delivery (optional)
    DELIVERY_EMAIL_ENABLED: bool = Field(default=False)
    DELIVERY_SMTP_ENABLED: bool = Field(default=False)
    DELIVERY_TEAMS_ENABLED: bool = Field(default=False)

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    TEAMS_WEBHOOK_URL: Optional[str] = None

    # App behavior
    EMAIL_MAX_THREADS: int = Field(default=200, ge=1, le=500)
    OUTPUT_DIR: Path = Field(default=Path("reports"))
    VIP_SENDERS_PATH: Path = Field(default=Path("config/vip.txt"))
    FEATURES_DRAFT_REPLIES: bool = Field(default=False)

    # Recipients
    RECIPIENTS: List[str] = Field(default_factory=list)


def load_config() -> AppSettings:
    settings = AppSettings()  # loads from env
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.GMAIL_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.MS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.GCAL_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    return settings
