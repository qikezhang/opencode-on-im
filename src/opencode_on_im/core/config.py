"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):
    """Telegram bot configuration."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    token: str | None = None
    parse_mode: str = "MarkdownV2"


class DingTalkSettings(BaseSettings):
    """DingTalk bot configuration."""

    model_config = SettingsConfigDict(env_prefix="DINGTALK_")

    app_key: str | None = None
    app_secret: str | None = None
    agent_id: str | None = None


class ProxySettings(BaseSettings):
    """Proxy configuration."""

    model_config = SettingsConfigDict(env_prefix="PROXY_")

    enabled: bool = False
    url: str | None = None


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="OPENCODE_IM_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    data_dir: Path = Field(default=Path("/data"))
    opencode_port: int = 4096
    opencode_host: str = "127.0.0.1"

    web_terminal: Literal["ttyd", "code-server"] = "ttyd"
    web_terminal_port: int = 7681

    message_image_threshold: int = 10
    max_offline_messages: int = 20
    image_width: int = 720
    image_font_size: int = 13

    secret_key: str = Field(default="change-me-in-production")

    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    dingtalk: DingTalkSettings = Field(default_factory=DingTalkSettings)
    proxy: ProxySettings = Field(default_factory=ProxySettings)

    upgrade_check_url: str = "https://api.opencode-cloudify.dev/v1/check-update"
    upgrade_check_enabled: bool = True


def load_settings(config_path: str | None = None) -> Settings:
    """Load settings from environment and optional config file."""
    if config_path:
        import yaml

        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        return Settings(**config_data)
    return Settings()
