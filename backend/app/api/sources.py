"""Sources management API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.custom_source import CustomSource
from app.services.domain_service import DomainService

router = APIRouter()


# Built-in sources registry
BUILTIN_SOURCES = {
    # Scientific databases
    "pubmed": {
        "id": "pubmed",
        "name": "PubMed",
        "description": "Biomedical and life sciences literature",
        "type": "database",
        "requiresApiKey": False,
        "domains": ["science", "health"],
    },
    "arxiv": {
        "id": "arxiv",
        "name": "arXiv",
        "description": "Physics, math, CS, and biology preprints",
        "type": "preprint",
        "requiresApiKey": False,
        "domains": ["science", "tech"],
    },
    "semantic_scholar": {
        "id": "semantic_scholar",
        "name": "Semantic Scholar",
        "description": "Cross-discipline with citations",
        "type": "database",
        "requiresApiKey": False,
        "domains": ["science", "tech"],
    },
    "biorxiv": {
        "id": "biorxiv",
        "name": "bioRxiv",
        "description": "Biology preprints",
        "type": "preprint",
        "requiresApiKey": False,
        "domains": ["science", "health"],
    },
    "medrxiv": {
        "id": "medrxiv",
        "name": "medRxiv",
        "description": "Medical and health sciences preprints",
        "type": "preprint",
        "requiresApiKey": False,
        "domains": ["science", "health"],
    },
    "plos": {
        "id": "plos",
        "name": "PLOS",
        "description": "Public Library of Science open access journals",
        "type": "journal",
        "requiresApiKey": False,
        "domains": ["science"],
    },
    # RSS feeds
    "nature_rss": {
        "id": "nature_rss",
        "name": "Nature",
        "description": "Nature journal RSS feed",
        "type": "journal_rss",
        "requiresApiKey": False,
        "domains": ["science"],
    },
    "science_rss": {
        "id": "science_rss",
        "name": "Science",
        "description": "Science journal RSS feed",
        "type": "journal_rss",
        "requiresApiKey": False,
        "domains": ["science"],
    },
    "lancet_rss": {
        "id": "lancet_rss",
        "name": "The Lancet",
        "description": "Medical journal RSS feed",
        "type": "journal_rss",
        "requiresApiKey": False,
        "domains": ["science", "health"],
    },
    "nejm_rss": {
        "id": "nejm_rss",
        "name": "NEJM",
        "description": "New England Journal of Medicine RSS feed",
        "type": "journal_rss",
        "requiresApiKey": False,
        "domains": ["science", "health"],
    },
    "bmj_rss": {
        "id": "bmj_rss",
        "name": "BMJ",
        "description": "British Medical Journal RSS feed",
        "type": "journal_rss",
        "requiresApiKey": False,
        "domains": ["science", "health"],
    },
}


class CustomSourceCreate(BaseModel):
    """Request model for creating a custom source."""
    name: str
    url: str
    description: Optional[str] = None
    credibility_base_score: float = 50.0
    is_peer_reviewed: bool = False


class CustomSourceUpdate(BaseModel):
    """Request model for updating a custom source."""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    credibility_base_score: Optional[float] = None
    is_peer_reviewed: Optional[bool] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all available sources for the active domain."""
    domain_service = DomainService(db)
    domain = await domain_service.get_active_domain()

    sources = []

    # Add built-in sources that are enabled for this domain
    enabled_source_ids = domain.enabled_sources or []
    for source_id, source_data in BUILTIN_SOURCES.items():
        # Check if source is relevant for this domain
        if domain.domain_id in source_data.get("domains", []):
            sources.append({
                **source_data,
                "isCustom": False,
                "isEnabled": source_id in enabled_source_ids,
            })

    # Add custom sources for this domain
    result = await db.execute(
        select(CustomSource).where(CustomSource.domain_id == domain.domain_id)
    )
    custom_sources = result.scalars().all()
    for cs in custom_sources:
        sources.append(cs.to_dict())

    return {
        "domainId": domain.domain_id,
        "sources": sources,
    }


@router.get("/builtin")
async def list_builtin_sources():
    """List all built-in sources."""
    return {
        "sources": list(BUILTIN_SOURCES.values()),
    }


@router.post("/custom")
async def create_custom_source(
    data: CustomSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a custom RSS feed source."""
    domain_service = DomainService(db)
    domain = await domain_service.get_active_domain()

    # Generate unique source_id
    source_id = f"custom_{domain.domain_id}_{data.name.lower().replace(' ', '_')}"

    # Check for duplicate
    existing = await db.execute(
        select(CustomSource).where(CustomSource.source_id == source_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source with this name already exists")

    source = CustomSource(
        domain_id=domain.domain_id,
        name=data.name,
        source_id=source_id,
        source_type="rss",
        url=data.url,
        description=data.description,
        credibility_base_score=data.credibility_base_score,
        is_peer_reviewed=data.is_peer_reviewed,
    )

    db.add(source)
    await db.commit()
    await db.refresh(source)

    return source.to_dict()


@router.get("/custom/{source_id}")
async def get_custom_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Get a custom source by ID."""
    result = await db.execute(
        select(CustomSource).where(CustomSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return source.to_dict()


@router.put("/custom/{source_id}")
async def update_custom_source(
    source_id: int,
    data: CustomSourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a custom source."""
    result = await db.execute(
        select(CustomSource).where(CustomSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)

    return source.to_dict()


@router.delete("/custom/{source_id}")
async def delete_custom_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a custom source."""
    result = await db.execute(
        select(CustomSource).where(CustomSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()

    return {"message": "Source deleted successfully"}


@router.post("/custom/{source_id}/test")
async def test_custom_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Test a custom RSS feed source."""
    import feedparser

    result = await db.execute(
        select(CustomSource).where(CustomSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        feed = feedparser.parse(source.url)

        if feed.bozo and feed.bozo_exception:
            return {
                "success": False,
                "error": str(feed.bozo_exception),
                "entries": 0,
            }

        entries = []
        for entry in feed.entries[:5]:
            entries.append({
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            })

        return {
            "success": True,
            "feedTitle": feed.feed.get("title", source.name),
            "entriesCount": len(feed.entries),
            "sampleEntries": entries,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "entries": 0,
        }
