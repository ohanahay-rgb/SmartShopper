"""SmartShopper configuration -- nested Pydantic Settings with @lru_cache singleton.

Patterns from: tg-bot-fastapi-aiogram (@final + @lru_cache)
               dev-pro-agents (nested settings + @model_validator)
"""

from __future__ import annotations

from functools import lru_cache
from typing import final

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = "localhost"
    port: int = 5432
    db: str = "smartshopper"
    user: str = "smartshopper"
    password: str = "localdev"

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


@final
class RedisSettings(BaseSettings):
    """Redis connection settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


@final
class TelegramSettings(BaseSettings):
    """Telegram bot settings."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    bot_token: str = ""
    webhook_url: str = ""
    webhook_path: str = "/webhook/telegram"
    secret_token: str = ""


@final
class LLMSettings(BaseSettings):
    """LLM API keys and model selections."""

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    supervisor_model: str = "claude-opus-4-6"
    worker_model: str = "gpt-4o-mini"


@final
class GoogleSettings(BaseSettings):
    """Google APIs settings."""

    maps_api_key: str = Field(default="", alias="GOOGLE_MAPS_API_KEY")


@final
class EmailSettings(BaseSettings):
    """Email / SendGrid settings for daily reports."""

    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    report_email: str = Field(default="", alias="REPORT_EMAIL")


@final
class Settings(BaseSettings):
    """Root settings -- loads .env and nests all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "SmartShopper"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Budget control
    daily_budget_usd: float = Field(default=50.0, alias="DAILY_BUDGET_USD")
    budget_warning_threshold: float = 0.80
    budget_block_threshold: float = 0.95

    # Nested sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    google: GoogleSettings = Field(default_factory=GoogleSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        """Enforce required keys in production."""
        if self.environment == "production":
            if not self.telegram.bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN is required in production")
            if not self.llm.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton -- call this everywhere instead of Settings()."""
    return Settings()
