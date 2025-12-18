"""Data models for the Bakery Quotation Agent"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class QuoteState:
    """Tracks the current state of quote generation"""

    # Required fields
    job_type: str | None = None
    quantity: int | None = None
    customer_name: str | None = None
    due_date: str | None = None

    # Optional fields with defaults
    company_name: str = "The Artisan Bakery"
    currency: str = "GBP"
    vat_pct: float = 20.0
    markup_pct: float = 30.0
    labor_rate: float = 15.0
    notes: str = ""

    # Internal state
    bom_data: dict[str, Any] | None = None
    material_costs: dict[str, Any] | None = None
    calculations: dict[str, Any] | None = None
    quote_id: str | None = None

    def is_complete(self) -> bool:
        """Check if all required fields are filled"""
        return all([
            self.job_type,
            self.quantity,
            self.customer_name,
            self.due_date
        ])

    def get_missing_fields(self) -> list[str]:
        """Return list of missing required fields"""
        missing = []
        if not self.job_type:
            missing.append("job_type")
        if not self.quantity:
            missing.append("quantity")
        if not self.customer_name:
            missing.append("customer_name")
        if not self.due_date:
            missing.append("due_date")
        return missing

    def generate_quote_id(self) -> str:
        """Generate unique quote ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.quote_id = f"Q{timestamp}"
        return self.quote_id

    def get_quote_date(self) -> str:
        """Get current date in ISO format"""
        return datetime.now().strftime("%Y-%m-%d")

    def get_valid_until(self, days: int = 30) -> str:
        """Calculate quote validity date"""
        valid_date = datetime.now() + timedelta(days=days)
        return valid_date.strftime("%Y-%m-%d")

    def reset(self) -> None:
        """Reset state for new quote"""
        self.job_type = None
        self.quantity = None
        self.customer_name = None
        self.due_date = None
        self.notes = ""
        self.bom_data = None
        self.material_costs = None
        self.calculations = None
        self.quote_id = None


@dataclass
class MaterialLine:
    """Material line item for quote"""
    name: str
    qty: float
    unit: str
    unit_cost: float
    line_cost: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template"""
        return {
            'name': self.name,
            'qty': f"{self.qty:.2f}",
            'unit': self.unit,
            'unit_cost': f"{self.unit_cost:.2f}",
            'line_cost': f"{self.line_cost:.2f}"
        }


# Exceptions
class QuoteGenerationError(Exception):
    """Base exception for quote generation"""
    pass


class MissingMaterialError(QuoteGenerationError):
    """Material not found in database"""
    pass


class APIConnectionError(QuoteGenerationError):
    """Cannot connect to BOM API"""
    pass


class ValidationError(QuoteGenerationError):
    """Invalid input data"""
    pass
