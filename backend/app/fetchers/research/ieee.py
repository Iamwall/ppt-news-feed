"""IEEE Xplore API fetcher.

https://developer.ieee.org/
Requires API key.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class IEEEFetcher(BaseFetcher):
    """Fetcher for IEEE Xplore digital library."""
    
    source_name = "ieee"
    rate_limit = 1.0
    
    BASE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("IEEE_KEY")
        if not self.api_key:
            raise ValueError("IEEE_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from IEEE Xplore."""
        await self._rate_limit()
        
        params = {
            "apikey": self.api_key,
            "max_records": min(max_results, 200),
            "sort_order": "desc",
            "sort_field": "publication_date",
        }
        
        if keywords:
            params["querytext"] = " OR ".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=60.0)
            response.raise_for_status()
            data = response.json()
        
        for article in data.get("articles", []):
            title = article.get("title")
            if not title:
                continue
            
            authors = [AuthorData(name=a.get("full_name", "")) for a in article.get("authors", {}).get("authors", [])[:10]]
            
            pub_date = None
            if article.get("publication_date"):
                try:
                    pub_date = datetime.strptime(article["publication_date"], "%Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            yield PaperData(
                title=title,
                abstract=article.get("abstract"),
                authors=authors,
                source=self.source_name,
                source_id=str(article.get("article_number", "")),
                journal=article.get("publication_title"),
                doi=article.get("doi"),
                url=article.get("html_url"),
                published_date=pub_date,
                citations=article.get("citing_paper_count"),
                is_peer_reviewed=True,
                is_preprint=False,
                raw_data={"content_type": article.get("content_type")}
            )
