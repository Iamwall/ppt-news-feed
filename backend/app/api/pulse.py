"""Live Pulse API endpoints for real-time feed."""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.paper import Paper
from app.services.live_pulse_service import LivePulseService
from app.services.breaking_detector import detect_breaking_news


router = APIRouter()


# Pydantic schemas for responses
class PaperPulseResponse(BaseModel):
    """Paper response for Live Pulse feed."""
    id: int
    title: str
    abstract: Optional[str] = None
    source: str
    url: Optional[str] = None
    published_date: Optional[datetime] = None

    # Pulse-specific fields
    is_breaking: bool = False
    breaking_score: Optional[float] = None
    breaking_keywords: Optional[List[str]] = None
    freshness_score: Optional[float] = None
    triage_status: Optional[str] = None
    triage_score: Optional[float] = None

    # Timestamps
    fetched_at: datetime

    class Config:
        from_attributes = True


class FeedStatsResponse(BaseModel):
    """Statistics about the live feed."""
    time_window_hours: int
    total_papers: int
    breaking_count: int
    passed_triage_count: int
    avg_freshness_score: float
    breaking_rate: float


class RefreshResponse(BaseModel):
    """Response from refresh operation."""
    papers_updated: int
    new_breaking: int
    time_window_hours: int


# Helper function to convert Paper to response
def paper_to_response(paper: Paper) -> PaperPulseResponse:
    """Convert Paper model to API response."""
    return PaperPulseResponse(
        id=paper.id,
        title=paper.title,
        abstract=paper.abstract[:500] if paper.abstract else None,
        source=paper.source,
        url=paper.url,
        published_date=paper.published_date,
        is_breaking=paper.is_breaking or False,
        breaking_score=paper.breaking_score,
        breaking_keywords=paper.breaking_keywords,
        freshness_score=paper.freshness_score,
        triage_status=paper.triage_status,
        triage_score=paper.triage_score,
        fetched_at=paper.fetched_at,
    )


@router.get("/feed", response_model=List[PaperPulseResponse])
async def get_live_feed(
    domain_id: Optional[str] = Query(None, description="Filter by domain"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    breaking_only: bool = Query(False, description="Only return breaking news"),
    passed_triage_only: bool = Query(True, description="Only return items that passed triage"),
    min_freshness: float = Query(0.0, ge=0.0, le=1.0, description="Minimum freshness score"),
    db: AsyncSession = Depends(get_db)
):
    """Get the live pulse feed.

    Returns papers sorted by:
    1. Breaking status (breaking news first)
    2. Breaking score (higher urgency first)
    3. Freshness score (newer items first)

    This endpoint supports pagination and filtering.
    """
    service = LivePulseService(db)

    papers = await service.get_feed(
        domain_id=domain_id,
        limit=limit,
        offset=offset,
        breaking_only=breaking_only,
        passed_triage_only=passed_triage_only,
        min_freshness=min_freshness,
    )

    return [paper_to_response(p) for p in papers]


@router.get("/breaking", response_model=List[PaperPulseResponse])
async def get_breaking_news(
    domain_id: Optional[str] = Query(None, description="Filter by domain"),
    limit: int = Query(10, ge=1, le=50, description="Maximum items to return"),
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours"),
    db: AsyncSession = Depends(get_db)
):
    """Get current breaking news.

    Returns only items flagged as breaking news within the specified time window.
    Sorted by breaking score (most urgent first).
    """
    service = LivePulseService(db)

    papers = await service.get_breaking_news(
        domain_id=domain_id,
        limit=limit,
        max_age_hours=max_age_hours,
    )

    return [paper_to_response(p) for p in papers]


@router.get("/stats", response_model=FeedStatsResponse)
async def get_feed_stats(
    domain_id: Optional[str] = Query(None, description="Filter by domain"),
    hours_back: int = Query(24, ge=1, le=168, description="Time window in hours"),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about the live feed.

    Returns counts and metrics about recent papers,
    breaking news, and triage status.
    """
    service = LivePulseService(db)

    stats = await service.get_feed_stats(
        domain_id=domain_id,
        hours_back=hours_back,
    )

    return FeedStatsResponse(**stats)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_breaking_scores(
    domain_id: Optional[str] = Query(None, description="Filter by domain"),
    hours_back: int = Query(48, ge=1, le=168, description="How far back to refresh"),
    db: AsyncSession = Depends(get_db)
):
    """Refresh breaking news and freshness scores.

    Re-analyzes recent papers to update their breaking news status
    and freshness scores. This should be called periodically to keep
    the feed current as time-decay affects scores.

    Returns statistics about updated papers.
    """
    service = LivePulseService(db)

    result = await service.refresh_breaking_scores(
        domain_id=domain_id,
        hours_back=hours_back,
    )

    return RefreshResponse(**result)


@router.get("/new", response_model=List[PaperPulseResponse])
async def get_new_items(
    since: datetime = Query(..., description="Get items newer than this timestamp"),
    domain_id: Optional[str] = Query(None, description="Filter by domain"),
    passed_triage_only: bool = Query(True, description="Only return items that passed triage"),
    db: AsyncSession = Depends(get_db)
):
    """Get new items since a specific time.

    Used for polling-based updates when WebSocket isn't available.
    Returns all items added after the specified timestamp.

    The client should track the latest timestamp received and use
    that for subsequent requests.
    """
    service = LivePulseService(db)

    papers = await service.get_new_items_since(
        since=since,
        domain_id=domain_id,
        passed_triage_only=passed_triage_only,
    )

    return [paper_to_response(p) for p in papers]


@router.post("/analyze/{paper_id}")
async def analyze_paper_breaking(
    paper_id: int,
    domain_id: str = Query("news", description="Domain context for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """Analyze a specific paper for breaking news status.

    Useful for testing or manually triggering analysis
    on a single paper.
    """
    from sqlalchemy import select

    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if not paper:
        return {"error": "Paper not found", "paper_id": paper_id}

    # Analyze
    analysis_result = await detect_breaking_news([paper], domain_id, db)

    analysis = analysis_result["results"][0] if analysis_result["results"] else None

    return {
        "paper_id": paper_id,
        "title": paper.title,
        "is_breaking": paper.is_breaking,
        "breaking_score": paper.breaking_score,
        "breaking_keywords": paper.breaking_keywords,
        "freshness_score": paper.freshness_score,
        "analysis": {
            "keywords_found": analysis.keywords_found if analysis else [],
            "signals": analysis.signals if analysis else {},
        } if analysis else None
    }
