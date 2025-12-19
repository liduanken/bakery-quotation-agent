"""Quotation API endpoints."""

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from src.app.data_models.common import ErrorResponse, QuoteRequest, QuoteResponse, StatusEnum
from src.app.services.quotation import QuotationService

router = APIRouter(prefix="/quotes", tags=["quotations"])

# Initialize service
quotation_service = QuotationService()


@router.post(
    "",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_quote(request: QuoteRequest) -> QuoteResponse:
    """
    Generate a new bakery quotation.

    This endpoint generates a complete quotation including:
    - Bill of materials from BOM API
    - Material costs from database
    - Labor calculations
    - Pricing with markup and VAT
    - Formatted quote document

    Args:
        request: Quote request with customer and order details

    Returns:
        QuoteResponse with quote ID and file path

    Raises:
        HTTPException: If materials not found or BOM unavailable
    """
    try:
        logger.info(f"Creating quote for {request.customer_name}: {request.quantity} × {request.job_type}")
        quote = await quotation_service.generate_quote(request)
        return quote

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating quote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quotation"
        )


@router.get("/job-types", response_model=list[str], tags=["quotations"])
async def get_job_types() -> list[str]:
    """Get available job types from BOM API."""
    try:
        job_types = quotation_service.bom_tool.get_job_types()
        return job_types
    except Exception as e:
        logger.error(f"Error fetching job types: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BOM API unavailable"
        )
