"""Application configuration loaded from environment variables."""
from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(default="my_vpn_bot", alias="BOT_USERNAME")
    support_username: str = Field(default="my_support", alias="SUPPORT_USERNAME")
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./vpn_bot.db", alias="DATABASE_URL"
    )

    # Marzban
    marzban_base_url: str = Field(default="", alias="MARZBAN_BASE_URL")
    marzban_username: str = Field(default="", alias="MARZBAN_USERNAME")
    marzban_password: str = Field(default="", alias="MARZBAN_PASSWORD")
    marzban_default_proxies_raw: str = Field(
        default='{"vless": {}}', alias="MARZBAN_DEFAULT_PROXIES"
    )
    marzban_default_inbounds_raw: str = Field(
        default="{}", alias="MARZBAN_DEFAULT_INBOUNDS"
    )

    # YooKassa
    yookassa_shop_id: str = Field(default="", alias="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str = Field(default="", alias="YOOKASSA_SECRET_KEY")
    yookassa_webhook_secret: str = Field(default="", alias="YOOKASSA_WEBHOOK_SECRET")

    # Webhook server
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, alias="WEBHOOK_PORT")

    # Trial plan
    trial_plan_name: str = Field(default="Пробный", alias="TRIAL_PLAN_NAME")
    trial_traffic_gb: int = Field(default=5, alias="TRIAL_TRAFFIC_GB")
    trial_days: int = Field(default=7, alias="TRIAL_DAYS")

    @property
    def admin_ids(self) -> set[int]:
        result: set[int] = set()
        for chunk in self.admin_ids_raw.replace(";", ",").split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                result.add(int(chunk))
        return result

    @property
    def marzban_default_proxies(self) -> dict:
        try:
            return json.loads(self.marzban_default_proxies_raw)
        except (json.JSONDecodeError, TypeError):
            return {"vless": {}}

    @property
    def marzban_default_inbounds(self) -> dict:
        try:
            return json.loads(self.marzban_default_inbounds_raw)
        except (json.JSONDecodeError, TypeError):
            return {}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
