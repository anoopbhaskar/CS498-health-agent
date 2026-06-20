"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


ROOT_DIR = Path(__file__).resolve().parent.parent


def env_value(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


@dataclass(frozen=True)
class Settings:
    app_name: str = env_value("APP_NAME", "FitAgent") or "FitAgent"
    environment: str = env_value("ENVIRONMENT", "local") or "local"
    database_url: str = env_value(
        "DATABASE_URL",
        f"sqlite:///{ROOT_DIR / 'var' / 'fitagent.sqlite3'}",
    ) or f"sqlite:///{ROOT_DIR / 'var' / 'fitagent.sqlite3'}"
    log_level: str = env_value("LOG_LEVEL", "INFO") or "INFO"
    anthropic_api_key: str | None = env_value("ANTHROPIC_API_KEY")
    agent_model: str = env_value("AGENT_MODEL", "local-rules-v1") or "local-rules-v1"
    max_memory_messages: int = int(env_value("MAX_MEMORY_MESSAGES", "12") or "12")


settings = Settings()
