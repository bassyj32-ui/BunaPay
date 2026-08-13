"""BunaPay configuration loader.

Loads secrets from .env (via python-dotenv). Fails fast on missing
required keys so the bot never starts half-configured.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when a required setting is missing or invalid."""


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required env var: {name} (see .env.template)")
    return value


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _require_int(name: str) -> int:
    try:
        return int(_require(name))
    except ValueError as exc:
        raise ConfigError(f"Env var {name} must be an integer") from exc


def _require_float(name: str) -> float:
    try:
        return float(_require(name))
    except ValueError as exc:
        raise ConfigError(f"Env var {name} must be a number") from exc


class Config:
    """Typed access to all BunaPay settings."""

    def __init__(self) -> None:
        self.telegram_bot_token: str = _require("TELEGRAM_BOT_TOKEN")
        self.telegram_admin_id: int = _require_int("TELEGRAM_ADMIN_ID")

        self.supabase_url: str = _require("SUPABASE_URL")
        self.supabase_service_key: str = _require("SUPABASE_SERVICE_KEY")

        self.telebirr_name: str = _require("TELEBIRR_NAME")
        self.telebirr_number: str = _require("TELEBIRR_NUMBER")

        # Optional
        self.sentry_dsn: str | None = _optional("SENTRY_DSN")
        self.mini_app_url: str | None = _optional("MINI_APP_URL")

    @property
    def sentry_enabled(self) -> bool:
        return self.sentry_dsn is not None


config = Config()
