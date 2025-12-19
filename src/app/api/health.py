"""Health endpoint definitions."""

from datetime import UTC, datetime

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """Schema returned by the health endpoint."""

    status: str = Field(default="ok")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    database: str = Field(default="unknown", description="Database connectivity status")
    bom_api: str = Field(default="unknown", description="BOM API connectivity status")


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/healthz", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def read_health() -> HealthResponse:
    """Return basic service health information."""

    # Check database
    try:
        import sqlite3
        from app.config import settings

        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Check BOM API
    try:
        import httpx
        from app.config import settings

        response = httpx.get(f"{settings.bom_api_url}/healthz", timeout=2.0)
        bom_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        bom_status = "unhealthy"

    return HealthResponse(database=db_status, bom_api=bom_status)
