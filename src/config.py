"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "FitAgent")
    environment: str = os.getenv("ENVIRONMENT", "local")
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{ROOT_DIR / 'var' / 'fitagent.sqlite3'}",
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    agent_model: str = os.getenv("AGENT_MODEL", "local-rules-v1")
    max_memory_messages: int = int(os.getenv("MAX_MEMORY_MESSAGES", "12"))


settings = Settings()
