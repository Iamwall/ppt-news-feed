"""Paper fetchers for various scientific databases."""
from app.fetchers.base import BaseFetcher, PaperData
from app.fetchers.pubmed import PubMedFetcher
from app.fetchers.arxiv import ArxivFetcher
from app.fetchers.biorxiv import BioRxivFetcher
from app.fetchers.semantic_scholar import SemanticScholarFetcher
from app.fetchers.plos import PLOSFetcher
from app.fetchers.rss_feeds import (
    NatureRSSFetcher,
    ScienceRSSFetcher,
    CellRSSFetcher,
    PLOSBiologyRSSFetcher,
    LancetRSSFetcher,
    NEJMRSSFetcher,
    BMJRSSFetcher,
)

__all__ = [
    "BaseFetcher",
    "PaperData",
    "PubMedFetcher",
    "ArxivFetcher",
    "BioRxivFetcher",
    "SemanticScholarFetcher",
    "PLOSFetcher",
    "NatureRSSFetcher",
    "ScienceRSSFetcher",
    "CellRSSFetcher",
    "PLOSBiologyRSSFetcher",
    "LancetRSSFetcher",
    "NEJMRSSFetcher",
    "BMJRSSFetcher",
]

# Factory for getting fetcher by source name
FETCHER_REGISTRY = {
    # Major research databases
    "pubmed": PubMedFetcher,
    "arxiv": ArxivFetcher,
    "semantic_scholar": SemanticScholarFetcher,

    # Preprint servers
    "biorxiv": BioRxivFetcher,
    "medrxiv": BioRxivFetcher,  # Same API, different server param

    # Open access journals
    "plos": PLOSFetcher,
    "plos_biology_rss": PLOSBiologyRSSFetcher,

    # High-impact journal RSS feeds
    "nature_rss": NatureRSSFetcher,
    "science_rss": ScienceRSSFetcher,
    "cell_rss": CellRSSFetcher,
    "lancet_rss": LancetRSSFetcher,
    "nejm_rss": NEJMRSSFetcher,
    "bmj_rss": BMJRSSFetcher,
}


def get_fetcher(source: str) -> BaseFetcher:
    """Get the appropriate fetcher for a source."""
    if source not in FETCHER_REGISTRY:
        raise ValueError(f"Unknown source: {source}")
    
    # Special handling for biorxiv/medrxiv which need the server parameter
    if source in ("biorxiv", "medrxiv"):
        return BioRxivFetcher(server=source)
    
    return FETCHER_REGISTRY[source]()
