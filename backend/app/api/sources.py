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


# Built-in sources registry - synchronized with app.fetchers
BUILTIN_SOURCES = {
    # === SCIENTIFIC RESEARCH ===
    "pubmed": {
        "id": "pubmed", "name": "PubMed", "category": "scientific",
        "description": "Biomedical and life sciences literature",
        "type": "database", "requiresApiKey": False,
    },
    "arxiv": {
        "id": "arxiv", "name": "arXiv", "category": "scientific",
        "description": "Physics, math, CS, and biology preprints",
        "type": "preprint", "requiresApiKey": False,
    },
    "semantic_scholar": {
        "id": "semantic_scholar", "name": "Semantic Scholar", "category": "scientific",
        "description": "Cross-discipline with citations",
        "type": "database", "requiresApiKey": False,
    },
    "openalex": {
        "id": "openalex", "name": "OpenAlex", "category": "scientific",
        "description": "Open catalog of 200M+ scholarly papers",
        "type": "database", "requiresApiKey": False,
    },
    "crossref": {
        "id": "crossref", "name": "Crossref", "category": "scientific",
        "description": "DOI metadata backbone",
        "type": "database", "requiresApiKey": False,
    },
    "doaj": {
        "id": "doaj", "name": "DOAJ", "category": "scientific",
        "description": "Directory of Open Access Journals",
        "type": "database", "requiresApiKey": False,
    },
    "biorxiv": {
        "id": "biorxiv", "name": "bioRxiv", "category": "scientific",
        "description": "Biology preprints",
        "type": "preprint", "requiresApiKey": False,
    },
    "medrxiv": {
        "id": "medrxiv", "name": "medRxiv", "category": "scientific",
        "description": "Medical preprints",
        "type": "preprint", "requiresApiKey": False,
    },
    "plos": {
        "id": "plos", "name": "PLOS", "category": "scientific",
        "description": "Public Library of Science",
        "type": "journal", "requiresApiKey": False,
    },
    "plos_biology_rss": {
        "id": "plos_biology_rss", "name": "PLOS Biology", "category": "scientific",
        "description": "PLOS Biology RSS Feed",
        "type": "journal_rss", "requiresApiKey": False,
    },
    "nature_rss": {"id": "nature_rss", "name": "Nature", "category": "scientific", "type": "journal_rss", "requiresApiKey": False},
    "science_rss": {"id": "science_rss", "name": "Science", "category": "scientific", "type": "journal_rss", "requiresApiKey": False},
    "cell_rss": {"id": "cell_rss", "name": "Cell", "category": "scientific", "type": "journal_rss", "requiresApiKey": False},
    "lancet_rss": {"id": "lancet_rss", "name": "The Lancet", "category": "scientific", "type": "journal_rss", "requiresApiKey": False},
    "nejm_rss": {"id": "nejm_rss", "name": "NEJM", "category": "scientific", "type": "journal_rss", "requiresApiKey": False},
    "bmj_rss": {"id": "bmj_rss", "name": "BMJ", "category": "scientific", "type": "journal_rss", "requiresApiKey": False},
    
    # === TECH & DEVELOPER ===
    "hackernews": {
        "id": "hackernews", "name": "Hacker News", "category": "tech",
        "description": "Tech and startup news",
        "type": "api", "requiresApiKey": False,
    },
    "github_trending": {
        "id": "github_trending", "name": "GitHub Trending", "category": "tech",
        "description": "Trending repositories",
        "type": "scraper", "requiresApiKey": False,
    },
    "devto": {
        "id": "devto", "name": "Dev.to", "category": "tech",
        "description": "Developer community articles",
        "type": "api", "requiresApiKey": False,
    },
    "stackexchange": {
        "id": "stackexchange", "name": "StackExchange", "category": "tech",
        "description": "Q&A communities",
        "type": "api", "requiresApiKey": False,
    },
    "producthunt": {
        "id": "producthunt", "name": "Product Hunt", "category": "tech",
        "description": "New product launches",
        "type": "api", "requiresApiKey": True,
    },
    "pytrends": {
        "id": "pytrends", "name": "Google Trends", "category": "tech",
        "description": "Search interest trends",
        "type": "scraper", "requiresApiKey": False,
    },
    
    # === NEWS & SOCIAL ===
    "reddit": {
        "id": "reddit", "name": "Reddit", "category": "news",
        "description": "Community discussions",
        "type": "api", "requiresApiKey": False,
    },
    "gdelt": {
        "id": "gdelt", "name": "GDELT", "category": "news",
        "description": "Global news database",
        "type": "api", "requiresApiKey": False,
    },
    "newsapi": {
        "id": "newsapi", "name": "NewsAPI", "category": "news",
        "description": "News aggregator API",
        "type": "api", "requiresApiKey": True,
    },
    "mediastack": {
        "id": "mediastack", "name": "Mediastack", "category": "news",
        "description": "Live news API",
        "type": "api", "requiresApiKey": True,
    },
    
    # === FINANCIAL ===
    "coingecko": {
        "id": "coingecko", "name": "CoinGecko", "category": "financial",
        "description": "Cryptocurrency trends",
        "type": "api", "requiresApiKey": False,
    },
    "worldbank": {
        "id": "worldbank", "name": "World Bank", "category": "financial",
        "description": "Global development data",
        "type": "api", "requiresApiKey": False,
    },
    "yahoo_finance": {
        "id": "yahoo_finance", "name": "Yahoo Finance", "category": "financial",
        "description": "Stock and market news",
        "type": "api", "requiresApiKey": False,
    },
    "finnhub": {
        "id": "finnhub", "name": "Finnhub", "category": "financial",
        "description": "Market news API",
        "type": "api", "requiresApiKey": True,
    },
    "alphavantage": {
        "id": "alphavantage", "name": "Alpha Vantage", "category": "financial",
        "description": "Stock sentiment API",
        "type": "api", "requiresApiKey": True,
    },
    "fred": {
        "id": "fred", "name": "FRED", "category": "financial",
        "description": "Federal Reserve data",
        "type": "api", "requiresApiKey": True,
    },
    
    # === HEALTH ===
    "openfda": {
        "id": "openfda", "name": "OpenFDA", "category": "health",
        "description": "Drug safety and recalls",
        "type": "api", "requiresApiKey": False,
    },
    "clinicaltrials": {
        "id": "clinicaltrials", "name": "ClinicalTrials.gov", "category": "health",
        "description": "Clinical trial data",
        "type": "api", "requiresApiKey": False,
    },
    "europepmc": {
        "id": "europepmc", "name": "Europe PMC", "category": "health",
        "description": "European biomedical literature",
        "type": "database", "requiresApiKey": False,
    },
    
    # === NEW SCIENTIFIC ===
    "zenodo": {
        "id": "zenodo", "name": "Zenodo", "category": "scientific",
        "description": "General-purpose open database",
        "type": "database", "requiresApiKey": False,
    },
    "ssrn": {
        "id": "ssrn", "name": "SSRN", "category": "scientific",
        "description": "Social Science Research Network",
        "type": "preprint", "requiresApiKey": False,
    },
    "philpapers": {
        "id": "philpapers", "name": "PhilPapers", "category": "scientific",
        "description": "Index of philosophy literature",
        "type": "database", "requiresApiKey": False,
    },
    "paperswithcode": {
        "id": "paperswithcode", "name": "Papers with Code", "category": "scientific",
        "description": "ML papers with code implementations",
        "type": "database", "requiresApiKey": False,
    },
    "unpaywall": {
        "id": "unpaywall", "name": "Unpaywall", "category": "scientific",
        "description": "Open access database",
        "type": "database", "requiresApiKey": True,
    },
    "core": {
        "id": "core", "name": "CORE", "category": "scientific",
        "description": "Aggregator of open access papers",
        "type": "database", "requiresApiKey": True,
    },
    "nasaads": {
        "id": "nasaads", "name": "NASA ADS", "category": "scientific",
        "description": "Astrophysics Data System",
        "type": "database", "requiresApiKey": True,
    },
    "springer": {
        "id": "springer", "name": "Springer", "category": "scientific",
        "description": "Springer Nature content",
        "type": "journal", "requiresApiKey": True,
    },
    "elsevier": {
        "id": "elsevier", "name": "Elsevier", "category": "scientific",
        "description": "ScienceDirect content",
        "type": "journal", "requiresApiKey": True,
    },

    # === NEW TECH ===
    "lobsters": {
        "id": "lobsters", "name": "Lobsters", "category": "tech",
        "description": "Tech news community",
        "type": "api", "requiresApiKey": False,
    },
    "haxor": {
        "id": "haxor", "name": "Haxor News", "category": "tech",
        "description": "Hacker News terminal reader source",
        "type": "scraper", "requiresApiKey": False,
    },
    "huggingface": {
        "id": "huggingface", "name": "Hugging Face", "category": "tech",
        "description": "Daily papers and models",
        "type": "api", "requiresApiKey": False,
    },
    "librariesio": {
        "id": "librariesio", "name": "Libraries.io", "category": "tech",
        "description": "Open source dependency data",
        "type": "api", "requiresApiKey": True,
    },
    "kaggle": {
        "id": "kaggle", "name": "Kaggle", "category": "tech",
        "description": "Data science community",
        "type": "api", "requiresApiKey": True,
    },

    # === NEW NEWS ===
    "wikinews": {
        "id": "wikinews", "name": "Wikinews", "category": "news",
        "description": "Collaborative news source",
        "type": "api", "requiresApiKey": False,
    },
    "datagov": {
        "id": "datagov", "name": "Data.gov", "category": "news",
        "description": "US Government open data",
        "type": "database", "requiresApiKey": False,
    },
    "praw": {
        "id": "praw", "name": "Reddit (PRAW)", "category": "news",
        "description": "Reddit via Official API",
        "type": "api", "requiresApiKey": True,
    },

    # === NEW FINANCIAL ===
    "sec_edgar": {
        "id": "sec_edgar", "name": "SEC Edgar", "category": "financial",
        "description": "US Corporate Filings",
        "type": "database", "requiresApiKey": False,
    },
    "cryptocompare": {
        "id": "cryptocompare", "name": "CryptoCompare", "category": "financial",
        "description": "Crypto market data",
        "type": "api", "requiresApiKey": False,
    },
    "iexcloud": {
        "id": "iexcloud", "name": "IEX Cloud", "category": "financial",
        "description": "Institutional grade financial data",
        "type": "api", "requiresApiKey": True,
    },
    "polygon": {
        "id": "polygon", "name": "Polygon.io", "category": "financial",
        "description": "Real-time stock data",
        "type": "api", "requiresApiKey": True,
    },
    "openbb": {
        "id": "openbb", "name": "OpenBB", "category": "financial",
        "description": "Investment research platform",
        "type": "api", "requiresApiKey": True,
    },

    # === NEW HEALTH ===
    "who": {
        "id": "who", "name": "WHO", "category": "health",
        "description": "World Health Organization",
        "type": "database", "requiresApiKey": False,
    },
    "cdc": {
        "id": "cdc", "name": "CDC", "category": "health",
        "description": "Centers for Disease Control",
        "type": "database", "requiresApiKey": False,
    },
    "medlineplus": {
        "id": "medlineplus", "name": "MedlinePlus", "category": "health",
        "description": "Trusted health information",
        "type": "database", "requiresApiKey": False,
    },
}


class CustomSourceCreate(BaseModel):
    """Request model for creating a custom source."""
    name: str
    url: str
    description: Optional[str] = None
    credibility_base_score: float = 50.0
    is_peer_reviewed: bool = False
    is_validated: bool = False
    verification_method: Optional[str] = None


class CustomSourceUpdate(BaseModel):
    """Request model for updating a custom source."""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    credibility_base_score: Optional[float] = None
    is_peer_reviewed: Optional[bool] = None
    is_active: Optional[bool] = None
    is_validated: Optional[bool] = None
    verification_method: Optional[str] = None


@router.get("/")
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all available sources for the active domain."""
    domain_service = DomainService(db)
    domain = await domain_service.get_active_domain()

    sources = []

    # Add all built-in sources
    enabled_source_ids = domain.enabled_sources or []
    for source_id, source_data in BUILTIN_SOURCES.items():
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


@router.get("/categories")
async def list_categories():
    """List all source categories with their sources."""
    categories = {}
    for source_id, source_data in BUILTIN_SOURCES.items():
        category = source_data.get("category", "other")
        if category not in categories:
            categories[category] = []
        categories[category].append({
            "id": source_id,
            "name": source_data.get("name"),
            "description": source_data.get("description"),
            "requiresApiKey": source_data.get("requiresApiKey", False),
        })
    
    return {
        "categories": [
            {"id": cat, "name": cat.title(), "sources": sources}
            for cat, sources in categories.items()
        ],
        "totalSources": len(BUILTIN_SOURCES),
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
        is_validated=data.is_validated,
        verification_method=data.verification_method,
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
