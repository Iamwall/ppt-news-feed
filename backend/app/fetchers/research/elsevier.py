"""Elsevier ScienceDirect API fetcher.

https://dev.elsevier.com/
Requires API key.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class ElsevierFetcher(BaseFetcher):
    """Fetcher for Elsevier ScienceDirect."""
    
    source_name = "elsevier"
    rate_limit = 1.0
    
    BASE_URL = "https://api.elsevier.com/content/search/sciencedirect"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("ELSEVIER_KEY")
        if not self.api_key:
            raise ValueError("ELSEVIER_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch articles from ScienceDirect."""
        await self._rate_limit()
        
        query = " OR ".join(keywords) if keywords else "*"
        
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json",
        }
        
        params = {
            "query": query,
            "count": min(max_results, 100),
            "sort": "-date",
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        results = data.get("search-results", {}).get("entry", [])
        
        for entry in results:
            title = entry.get("dc:title")
            if not title:
                continue
            
            # Authors
            authors = []
            author_str = entry.get("dc:creator", "")
            if author_str:
                authors.append(AuthorData(name=author_str))
            
            # Parse date
            pub_date = None
            if entry.get("prism:coverDate"):
                try:
                    pub_date = datetime.strptime(entry["prism:coverDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            # Get DOI
            doi = entry.get("prism:doi")
            
            yield PaperData(
                title=title,
                abstract=entry.get("prism:teaser"),
                authors=authors,
                source=self.source_name,
                source_id=entry.get("dc:identifier", ""),
                journal=entry.get("prism:publicationName"),
                doi=doi,
                url=entry.get("link", [{}])[0].get("@href") if entry.get("link") else None,
                published_date=pub_date,
                is_peer_reviewed=True,
                is_preprint=False,
                raw_data={
                    "pii": entry.get("pii"),
                    "openAccess": entry.get("openaccess"),
                }
            )
