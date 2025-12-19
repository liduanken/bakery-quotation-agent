"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Bakery Quotation Agent")
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    docs_url: str = Field(default="/docs")
    api_prefix: str = Field(default="/api/v1")

    # OpenAI API
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # LLM Configuration
    model_name: str = Field(default="gpt-4-turbo-preview")
    model_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # File Paths
    database_path: str = Field(default="resources/materials.sqlite")
    template_path: str = Field(default="resources/quote_template.md")
    output_dir: str = Field(default="output")

    # External Services
    bom_api_url: str = Field(default="http://localhost:8000")

    # Business Rules
    labor_rate: float = Field(default=15.0, ge=0.0)
    markup_pct: float = Field(default=30.0, ge=0.0)
    vat_pct: float = Field(default=20.0, ge=0.0, le=100.0)
    default_currency: str = Field(default="GBP")
    quote_validity_days: int = Field(default=30, ge=1)

    def model_post_init(self, __context: dict[str, Any] | None) -> None:
        """Post-initialization validation."""
        self.cors_origins = [origin.rstrip("/") for origin in self.cors_origins]

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls) -> "Settings":
        """Return a cached settings instance for reuse across the app."""
        return cls()


settings = Settings.load()
