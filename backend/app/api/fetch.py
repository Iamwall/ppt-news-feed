"""Fetch operations API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import FetchRequest, FetchResponse, FetchStatus
from app.services.fetch_service import FetchService, execute_fetch_background

router = APIRouter()


@router.post("/", response_model=FetchResponse)
async def fetch_papers(
    request: FetchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Fetch papers from specified sources.

    Optionally enable AI triage to filter noise before saving.
    Triage is disabled by default for backward compatibility.
    """
    service = FetchService(db)

    # Start fetch operation
    fetch_job = await service.start_fetch(
        sources=request.sources,
        keywords=request.keywords,
        max_results=request.max_results,
        days_back=request.days_back,
    )

    # Run fetch in background (with optional triage)
    background_tasks.add_task(
        execute_fetch_background,
        fetch_job.id,
        request.sources,
        request.keywords,
        request.max_results,
        request.days_back,
        request.enable_triage,  # Optional triage
        request.triage_provider,
        request.triage_model,
        request.domain_id,
    )

    triage_msg = " with AI triage" if request.enable_triage else ""
    return FetchResponse(
        job_id=fetch_job.id,
        status=FetchStatus.RUNNING,
        message=f"Fetching from {len(request.sources)} sources{triage_msg}",
    )


@router.get("/status/{job_id}")
async def get_fetch_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get status of a fetch operation."""
    service = FetchService(db)
    status = await service.get_status(job_id)
    return status


@router.get("/sources")
async def list_sources():
    """List available paper sources."""
    # Import here to avoid circular dependencies if sources.py imports other things
    # But checking sources.py, it looks clean. Ideally, we'd move BUILTIN_SOURCES to a shared config.
    # For now, importing from app.api.sources is the most direct invalidation of the hardcoded list.
    from app.api.sources import BUILTIN_SOURCES
    
    return {
        "sources": list(BUILTIN_SOURCES.values())
    }
