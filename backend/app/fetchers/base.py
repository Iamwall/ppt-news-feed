"""Base fetcher class and common data structures."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, AsyncIterator
import asyncio

from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class AuthorData:
    """Standardized author information."""
    name: str
    affiliation: Optional[str] = None
    h_index: Optional[int] = None
    semantic_scholar_id: Optional[str] = None


@dataclass
class PaperData:
    """Standardized paper data from any source."""
    title: str
    abstract: Optional[str]
    authors: List[AuthorData]
    source: str
    source_id: str
    
    # Optional fields
    journal: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    
    # Metrics
    citations: Optional[int] = None
    influential_citations: Optional[int] = None
    altmetric_score: Optional[float] = None
    
    # Journal/publication info
    journal_impact_factor: Optional[float] = None
    is_peer_reviewed: bool = True
    is_preprint: bool = False
    
    # Raw data for debugging
    raw_data: Optional[dict] = field(default=None, repr=False)


class BaseFetcher(ABC):
    """Base class for all paper fetchers."""
    
    source_name: str = "unknown"
    rate_limit: float = 1.0  # Requests per second
    
    def __init__(self):
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait_time = (1.0 / self.rate_limit) - (now - self._last_request_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request_time = asyncio.get_event_loop().time()
    
    @abstractmethod
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from the source.
        
        Args:
            keywords: Search keywords (optional, fetches recent if None)
            max_results: Maximum number of papers to fetch
            days_back: How many days back to search
            
        Yields:
            PaperData objects for each fetched paper
        """
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _make_request(self, *args, **kwargs):
        """Make an HTTP request with retry logic.
        
        Override in subclasses to implement actual HTTP calls.
        """
        raise NotImplementedError
