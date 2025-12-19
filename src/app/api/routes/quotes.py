"""Quote file download endpoints."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from loguru import logger

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{filename}")
async def download_quote(filename: str):
    """Download a generated quote PDF file."""
    try:
        # Sanitize filename to prevent directory traversal
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check file extension
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files can be downloaded")
        
        # Try local file first
        file_path = Path("output") / filename
        
        # If file exists locally, serve it
        if file_path.exists():
            logger.info(f"Serving quote file from local: {file_path}")
            return FileResponse(
                path=str(file_path),
                media_type="application/pdf",
                filename=filename,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        
        # If GCS is enabled and file not found locally, redirect to GCS URL
        gcs_enabled = os.getenv("GCS_ENABLED", "false").lower() == "true"
        if gcs_enabled:
            bucket_name = os.getenv("GCS_BUCKET_NAME", "")
            if bucket_name:
                gcs_url = f"https://storage.googleapis.com/{bucket_name}/quotes/{filename}"
                logger.info(f"File not found locally, redirecting to GCS: {gcs_url}")
                return RedirectResponse(url=gcs_url, status_code=307)
        
        # File not found anywhere
        logger.warning(f"Quote file not found locally or in GCS: {filename}")
        raise HTTPException(status_code=404, detail="Quote file not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving quote file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
