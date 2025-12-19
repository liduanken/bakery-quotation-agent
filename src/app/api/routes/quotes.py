"""Quote file download endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
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
        
        # Construct file path
        file_path = Path("output") / filename
        
        # Check if file exists
        if not file_path.exists():
            logger.warning(f"Quote file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Quote file not found")
        
        logger.info(f"Serving quote file: {file_path}")
        
        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving quote file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
