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
    return {
        "sources": [
            # Major research databases
            {
                "id": "pubmed",
                "name": "PubMed",
                "description": "Biomedical and life sciences literature",
                "type": "database",
                "requires_api_key": False,
            },
            {
                "id": "arxiv",
                "name": "arXiv",
                "description": "Physics, math, CS, and biology preprints",
                "type": "preprint",
                "requires_api_key": False,
            },
            {
                "id": "semantic_scholar",
                "name": "Semantic Scholar",
                "description": "Cross-discipline with citations (rate-limited without API key)",
                "type": "database",
                "requires_api_key": False,
            },
            # Preprint servers
            {
                "id": "biorxiv",
                "name": "bioRxiv",
                "description": "Biology preprints",
                "type": "preprint",
                "requires_api_key": False,
            },
            {
                "id": "medrxiv",
                "name": "medRxiv",
                "description": "Medical and health sciences preprints",
                "type": "preprint",
                "requires_api_key": False,
            },
            # Open access journals
            {
                "id": "plos",
                "name": "PLOS",
                "description": "Public Library of Science open access journals",
                "type": "journal",
                "requires_api_key": False,
            },
            {
                "id": "plos_biology_rss",
                "name": "PLOS Biology",
                "description": "PLOS Biology journal RSS feed",
                "type": "journal_rss",
                "requires_api_key": False,
            },
            # High-impact journal RSS feeds
            {
                "id": "nature_rss",
                "name": "Nature",
                "description": "Nature journal RSS feed (impact factor: 64.8)",
                "type": "journal_rss",
                "requires_api_key": False,
            },
            {
                "id": "science_rss",
                "name": "Science",
                "description": "Science journal RSS feed (impact factor: 56.9)",
                "type": "journal_rss",
                "requires_api_key": False,
            },
            {
                "id": "cell_rss",
                "name": "Cell",
                "description": "Cell journal RSS feed (impact factor: 66.8)",
                "type": "journal_rss",
                "requires_api_key": False,
                "status": "unavailable",  # Currently blocked
            },
            {
                "id": "lancet_rss",
                "name": "The Lancet",
                "description": "The Lancet medical journal RSS feed (impact factor: 202.7)",
                "type": "journal_rss",
                "requires_api_key": False,
            },
            {
                "id": "nejm_rss",
                "name": "NEJM",
                "description": "New England Journal of Medicine RSS feed (impact factor: 176.1)",
                "type": "journal_rss",
                "requires_api_key": False,
            },
            {
                "id": "bmj_rss",
                "name": "BMJ",
                "description": "British Medical Journal RSS feed (impact factor: 93.6)",
                "type": "journal_rss",
                "requires_api_key": False,
            },
        ]
    }
