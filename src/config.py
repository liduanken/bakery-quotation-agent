"""Configuration management for the Bakery Quotation Agent"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration"""

    # API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Model Configuration
    model_name: str = "gpt-4-turbo-preview"
    model_temperature: float = 0.1

    # Paths
    database_path: str = "resources/materials.sqlite"
    template_path: str = "resources/quote_template.md"
    output_dir: str = "out"

    # BOM API
    bom_api_url: str = "http://localhost:8000"
    
    # Backend API URL (for generating PDF links)
    backend_url: str = "http://localhost:8001"
    
    # Google Cloud Storage
    gcs_enabled: bool = False
    gcs_bucket_name: str = ""

    # Pricing defaults
    labor_rate: float = 15.0
    markup_pct: float = 30.0
    vat_pct: float = 20.0
    currency: str = "GBP"
    company_name: str = "The Artisan Bakery"
    quote_valid_days: int = 30

    # Agent Configuration
    agent_max_iterations: int = 15
    agent_verbose: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        load_dotenv()

        return cls(
            # API Keys
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),

            # Model
            model_name=os.getenv("MODEL_NAME", "gpt-4-turbo-preview"),
            model_temperature=float(os.getenv("MODEL_TEMPERATURE", "0.1")),

            # Paths
            database_path=os.getenv("DATABASE_PATH", "resources/materials.sqlite"),
            template_path=os.getenv("TEMPLATE_PATH", "resources/quote_template.md"),
            output_dir=os.getenv("OUTPUT_DIR", "out"),

            # BOM API
            bom_api_url=os.getenv("BOM_API_URL", "http://localhost:8000"),
            backend_url=os.getenv("BACKEND_URL", "http://localhost:8001"),
            
            # Google Cloud Storage
            gcs_enabled=os.getenv("GCS_ENABLED", "false").lower() == "true",
            gcs_bucket_name=os.getenv("GCS_BUCKET_NAME", ""),

            # Pricing
            labor_rate=float(os.getenv("LABOR_RATE", "15.0")),
            markup_pct=float(os.getenv("MARKUP_PCT", "30.0")),
            vat_pct=float(os.getenv("VAT_PCT", "20.0")),
            currency=os.getenv("DEFAULT_CURRENCY", "GBP"),
            company_name=os.getenv("COMPANY_NAME", "The Artisan Bakery"),
            quote_valid_days=int(os.getenv("QUOTE_VALID_DAYS", "30")),

            # Agent
            agent_max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "15")),
            agent_verbose=os.getenv("AGENT_VERBOSE", "true").lower() == "true",
        )

    def validate(self) -> None:
        """Validate configuration"""
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError(
                "Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set"
            )

        if self.labor_rate <= 0:
            raise ValueError("LABOR_RATE must be positive")

        if self.markup_pct < 0:
            raise ValueError("MARKUP_PCT must be non-negative")

        if self.vat_pct < 0:
            raise ValueError("VAT_PCT must be non-negative")
