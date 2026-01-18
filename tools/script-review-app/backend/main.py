"""FastAPI application for Script Review."""

import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.auth import verify_token
from backend.config import settings
from backend.models import (
    Script, 
    ReviewRequest, 
    ReviewResponse,
    RejectionReason,
    StatsResponse
)
from backend.storage import storage
from backend.dj_profiles import dj_profiles

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Script Review API",
    description="API for reviewing AI-generated DJ scripts",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Mount static files
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")


@app.get("/")
async def root():
    """Serve the main application page."""
    index_path = frontend_path / "templates" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Script Review API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/scripts")
async def get_scripts(
    dj: str | None = Query(None, description="Filter by DJ name"),
    category: str | None = Query(None, description="Filter by category (weather, story, news, gossip, music)"),
    status: str | None = Query(None, description="Filter by status (pending, approved, rejected)"),
    weather_type: str | None = Query(None, description="Filter by weather type"),
    date_from: str | None = Query(None, description="Filter scripts from this date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter scripts to this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Scripts per page"),
    _: None = Depends(verify_token)
):
    """
    Get paginated list of scripts to review with advanced filtering.
    
    Args:
        dj: Optional DJ name filter
        category: Optional category filter
        status: Optional status filter (pending, approved, rejected)
        weather_type: Optional weather type filter
        date_from: Optional start date filter (YYYY-MM-DD)
        date_to: Optional end date filter (YYYY-MM-DD)
        page: Page number (default 1)
        page_size: Scripts per page (default 20, max 100)
        
    Returns:
        Paginated list with scripts and metadata
    """
    try:
        scripts, total_count = storage.list_scripts_filtered(
            dj_filter=dj, 
            category_filter=category,
            status_filter=status,
            weather_type_filter=weather_type,
            date_from=date_from,
            date_to=date_to,
            page=page, 
            page_size=page_size
        )
        logger.info(f"Retrieved {len(scripts)} scripts (page {page}, total: {total_count}, filters: DJ={dj}, category={category}, status={status})")
        
        return {
            "scripts": scripts,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_more": page * page_size < total_count
        }
    except Exception as e:
        logger.error(f"Error retrieving scripts: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving scripts: {str(e)}")


@app.post("/api/review", response_model=ReviewResponse)
async def review_script(
    review: ReviewRequest,
    _: None = Depends(verify_token)
):
    """
    Submit a review for a script (approve or reject).
    
    Args:
        review: Review request with decision
        
    Returns:
        ReviewResponse with status
    """
    try:
        if review.status == "approved":
            success = storage.approve_script(review.script_id)
        else:
            success = storage.reject_script(
                review.script_id,
                review.reason_id,
                review.custom_comment
            )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Script not found or could not be processed: {review.script_id}"
            )
        
        logger.info(f"Script {review.script_id} {review.status}")
        
        return ReviewResponse(
            success=True,
            message=f"Script {review.status} successfully",
            script_id=review.script_id,
            status=review.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing script: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing review: {str(e)}")


@app.get("/api/reasons", response_model=list[RejectionReason])
async def get_rejection_reasons(_: None = Depends(verify_token)):
    """
    Get list of pre-defined rejection reasons.
    
    Returns:
        List of rejection reasons
    """
    try:
        reasons = storage.get_rejection_reasons()
        logger.info(f"Retrieved {len(reasons)} rejection reasons")
        return reasons
    except Exception as e:
        logger.error(f"Error retrieving rejection reasons: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reasons: {str(e)}")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(_: None = Depends(verify_token)):
    """
    Get review statistics.
    
    Returns:
        Statistics about approved, rejected, and pending scripts
    """
    try:
        stats = storage.get_stats()
        logger.info(f"Retrieved stats: {stats.total_pending} pending, "
                   f"{stats.total_approved} approved, {stats.total_rejected} rejected")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.get("/api/djs")
async def get_djs(_: None = Depends(verify_token)):
    """
    Get list of all DJs with their profiles.
    
    Returns:
        List of DJ profiles with name, station, region, year range
    """
    try:
        djs = dj_profiles.get_all_djs()
        logger.info(f"Retrieved {len(djs)} DJ profiles")
        return {"djs": djs}
    except Exception as e:
        logger.error(f"Error retrieving DJs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving DJs: {str(e)}")


@app.get("/api/stats/detailed")
async def get_detailed_stats(_: None = Depends(verify_token)):
    """
    Get detailed statistics with category and approval rate breakdown.
    
    Returns:
        Detailed statistics including category distribution and approval rates
    """
    try:
        detailed_stats = storage.get_detailed_stats()
        logger.info(f"Retrieved detailed stats")
        return detailed_stats
    except Exception as e:
        logger.error(f"Error retrieving DJ profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving DJ profiles: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
