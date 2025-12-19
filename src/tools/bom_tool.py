"""BOM API tool for fetching bill of materials

Full implementation based on documentation/03_BOM_API_Tool.md
Provides typed interface to the FastAPI pricing service.
"""
import logging
import time
from enum import Enum
from typing import Literal

import httpx
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class JobType(str, Enum):
    """Available bakery job types"""
    CUPCAKES = "cupcakes"
    CAKE = "cake"
    PASTRY_BOX = "pastry_box"


class Material(BaseModel):
    """Material requirement"""
    name: str
    unit: Literal["kg", "L", "ml", "each"]
    qty: float = Field(gt=0)

    def __str__(self):
        return f"{self.name}: {self.qty} {self.unit}"


class EstimateRequest(BaseModel):
    """Request for BOM estimate"""
    job_type: str
    quantity: int = Field(gt=0)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class EstimateResponse(BaseModel):
    """BOM estimate response"""
    job_type: str
    quantity: int
    materials: list[Material]
    labor_hours: float = Field(ge=0)

    def get_material_names(self) -> list[str]:
        """Get list of material names"""
        return [m.name for m in self.materials]

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'job_type': self.job_type,
            'quantity': self.quantity,
            'materials': [m.dict() for m in self.materials],
            'labor_hours': self.labor_hours
        }


# ============================================================================
# Exceptions
# ============================================================================

class BOMAPIError(Exception):
    """Base exception for BOM API errors"""
    pass


class APIConnectionError(BOMAPIError):
    """Cannot connect to API"""
    pass


class InvalidJobTypeError(BOMAPIError):
    """Invalid job type specified"""
    pass


# ============================================================================
# BOM API Client
# ============================================================================

class BOMAPITool:
    """Client for Bakery Pricing/BOM API"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        """
        Initialize BOM API client.
        
        Args:
            base_url: Base URL of the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.Client | None = None

        # Verify connection on init
        self._verify_connection()

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client

    def close(self):
        """Close HTTP client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========================================================================
    # Connection Management
    # ========================================================================

    def _verify_connection(self):
        """Verify API is accessible - log warning but don't crash if unavailable"""
        try:
            response = self._get_client().get("/job-types")
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"Connected to BOM API at {self.base_url}")
            else:
                logger.warning(f"Unexpected job-types response: {data}")
        except httpx.ConnectError as e:
            logger.warning(
                f"Cannot connect to BOM API at {self.base_url}. "
                f"BOM pricing will not be available. "
                f"To enable it, ensure the service is running:\n"
                f"  cd resources/bakery_pricing_tool\n"
                f"  docker compose up --build"
            )
        except Exception as e:
            logger.warning(f"BOM API health check failed: {e}. BOM pricing may not be available.")

    def is_healthy(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self._get_client().get("/job-types")
            return response.status_code == 200 and isinstance(response.json(), list)
        except Exception:
            return False

    # ========================================================================
    # API Methods
    # ========================================================================

    def get_job_types(self) -> list[str]:
        """
        Get list of available job types.
        
        Returns:
            List of job type strings
            
        Raises:
            APIConnectionError: If cannot connect to API
        """
        try:
            response = self._get_client().get("/job-types")
            response.raise_for_status()

            job_types = response.json()
            logger.debug(f"Available job types: {job_types}")
            return job_types

        except httpx.HTTPError as e:
            raise APIConnectionError(f"Failed to get job types: {e}") from e

    def estimate(
        self,
        job_type: str,
        quantity: int
    ) -> EstimateResponse:
        """
        Get BOM estimate for a job.
        
        Args:
            job_type: Type of bakery item (cupcakes, cake, pastry_box)
            quantity: Number of items to produce
            
        Returns:
            EstimateResponse with materials and labor hours
            
        Raises:
            InvalidJobTypeError: If job type is not valid
            APIConnectionError: If cannot connect to API
            ValueError: If quantity is invalid
        """
        # Validate inputs
        if quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {quantity}")

        # Normalize job type
        job_type_lower = job_type.lower().replace(' ', '_')

        # Prepare request
        request_data = {
            "job_type": job_type_lower,
            "quantity": quantity
        }

        try:
            response = self._get_client().post(
                "/estimate",
                json=request_data
            )

            # Handle errors
            if response.status_code == 400:
                error_detail = response.json().get('detail', 'Unknown error')
                raise InvalidJobTypeError(f"Invalid job type '{job_type}': {error_detail}")

            response.raise_for_status()

            # Parse response
            data = response.json()
            estimate = EstimateResponse(**data)

            logger.info(
                f"BOM estimate: {quantity} × {job_type} → "
                f"{len(estimate.materials)} materials, {estimate.labor_hours}h labor"
            )

            return estimate

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise InvalidJobTypeError(f"Invalid job type: {job_type}") from e
            raise APIConnectionError(f"API error: {e}") from e
        except httpx.HTTPError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

    def estimate_with_retry(
        self,
        job_type: str,
        quantity: int
    ) -> EstimateResponse:
        """
        Get BOM estimate with automatic retries.
        
        Args:
            job_type: Type of bakery item
            quantity: Number of items
            
        Returns:
            EstimateResponse
            
        Raises:
            Same as estimate() after all retries exhausted
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self.estimate(job_type, quantity)
            except APIConnectionError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")

        raise last_error

    def estimate_multiple(
        self,
        estimates: list[tuple]
    ) -> list[EstimateResponse]:
        """
        Get multiple estimates (useful for comparing options).
        
        Args:
            estimates: List of (job_type, quantity) tuples
            
        Returns:
            List of EstimateResponse objects
        """
        results = []
        errors = []

        for job_type, quantity in estimates:
            try:
                result = self.estimate(job_type, quantity)
                results.append(result)
            except Exception as e:
                errors.append((job_type, quantity, str(e)))
                logger.error(f"Failed to get estimate for {job_type} × {quantity}: {e}")

        if errors:
            logger.warning(f"Failed {len(errors)} out of {len(estimates)} estimates")

        return results

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def format_estimate(self, estimate: EstimateResponse) -> str:
        """
        Format estimate for display.
        
        Args:
            estimate: EstimateResponse to format
            
        Returns:
            Formatted string
        """
        lines = [
            f"BOM Estimate for {estimate.quantity} × {estimate.job_type}",
            "",
            "Materials:",
        ]

        for material in estimate.materials:
            lines.append(f"  • {material.name}: {material.qty} {material.unit}")

        lines.extend([
            "",
            f"Labor: {estimate.labor_hours} hours",
        ])

        return "\n".join(lines)

    def estimate_summary(self, estimate: EstimateResponse) -> dict:
        """
        Get summary statistics for an estimate.
        
        Returns:
            Dictionary with summary data
        """
        return {
            'job_type': estimate.job_type,
            'quantity': estimate.quantity,
            'material_count': len(estimate.materials),
            'material_names': estimate.get_material_names(),
            'labor_hours': estimate.labor_hours,
            'materials_per_unit': len(estimate.materials),
            'labor_per_unit': estimate.labor_hours / estimate.quantity
        }

    def validate_job_type(self, job_type: str) -> bool:
        """
        Check if job type is valid.
        
        Args:
            job_type: Job type to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            valid_types = self.get_job_types()
            return job_type.lower() in [t.lower() for t in valid_types]
        except Exception:
            # If can't connect, check against known types
            return job_type.lower() in ['cupcakes', 'cake', 'pastry_box']
