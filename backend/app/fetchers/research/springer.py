"""Springer Nature API fetcher.

https://dev.springernature.com/
Requires API key.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class SpringerFetcher(BaseFetcher):
    """Fetcher for Springer Nature journals."""
    
    source_name = "springer"
    rate_limit = 1.0
    
    BASE_URL = "https://api.springernature.com/meta/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("SPRINGER_KEY")
        if not self.api_key:
            raise ValueError("SPRINGER_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch articles from Springer Nature."""
        await self._rate_limit()
        
        query = " OR ".join(keywords) if keywords else "*"
        
        params = {
            "api_key": self.api_key,
            "q": query,
            "p": min(max_results, 50),
            "s": 1,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/json",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        records = data.get("records", [])
        
        for record in records:
            title = record.get("title")
            if not title:
                continue
            
            # Authors
            authors = []
            for creator in record.get("creators", [])[:10]:
                name = creator.get("creator")
                if name:
                    authors.append(AuthorData(name=name))
            
            # Parse date
            pub_date = None
            if record.get("publicationDate"):
                try:
                    pub_date = datetime.strptime(record["publicationDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            yield PaperData(
                title=title,
                abstract=record.get("abstract"),
                authors=authors,
                source=self.source_name,
                source_id=record.get("identifier", ""),
                journal=record.get("publicationName"),
                doi=record.get("doi"),
                url=record.get("url", [{}])[0].get("value") if record.get("url") else None,
                published_date=pub_date,
                is_peer_reviewed=True,
                is_preprint=False,
                raw_data={
                    "openAccess": record.get("openAccess"),
                    "publisher": record.get("publisher"),
                }
            )
