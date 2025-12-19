"""Common data models for API responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    """Response status values."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class ErrorResponse(BaseModel):
    """Standard error response."""

    status: StatusEnum = Field(default=StatusEnum.FAILURE)
    error_code: str
    error_message: str
    details: dict[str, Any] | None = None


class QuoteRequest(BaseModel):
    """Request to generate a quotation."""

    job_type: str = Field(..., description="Type of bakery item (cupcakes, cake, etc.)")
    quantity: int = Field(..., gt=0, description="Number of items to produce")
    customer_name: str = Field(..., min_length=1, description="Customer name")
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Due date (YYYY-MM-DD)")
    company_name: str = Field(default="Artisan Bakery", description="Your company name")
    notes: str | None = Field(default=None, description="Additional notes")


class QuoteResponse(BaseModel):
    """Response containing quotation details."""

    status: StatusEnum = Field(default=StatusEnum.SUCCESS)
    quote_id: str
    file_path: str
    total: float
    currency: str = Field(default="GBP")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MaterialCostItem(BaseModel):
    """Material cost information."""

    name: str
    unit: str
    unit_cost: float
    currency: str = Field(default="GBP")


class BOMEstimate(BaseModel):
    """Bill of materials estimate."""

    job_type: str
    quantity: int
    materials: list[dict[str, Any]]
    labor_hours: float
