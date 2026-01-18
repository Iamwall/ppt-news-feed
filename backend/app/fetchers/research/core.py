"""CORE API fetcher for research papers.

https://core.ac.uk/services/api
Free access with registration. Rate limit: 10 req/10 sec.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class COREFetcher(BaseFetcher):
    """Fetcher for CORE - aggregates research from repositories worldwide."""
    
    source_name = "core"
    rate_limit = 1.0  # 10 req/10 sec
    
    BASE_URL = "https://api.core.ac.uk/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("CORE_API_KEY")
        # CORE has limited free access without key
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from CORE."""
        await self._rate_limit()
        
        # Build query
        if keywords:
            query = " OR ".join(keywords)
        else:
            query = "*"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        params = {
            "q": query,
            "limit": min(max_results, 100),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/works",
                params=params,
                headers=headers,
                timeout=60.0,
            )
            
            if response.status_code == 401:
                print("CORE API requires authentication. Set CORE_API_KEY.")
                return
            
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        
        for item in results:
            try:
                paper = self._parse_work(item)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing CORE work: {e}")
                continue
    
    def _parse_work(self, item: dict) -> Optional[PaperData]:
        """Parse a single CORE work."""
        title = item.get("title")
        if not title:
            return None
        
        # Authors
        authors = []
        for author in item.get("authors", [])[:10]:
            name = author.get("name")
            if name:
                authors.append(AuthorData(name=name))
        
        # Publication date
        pub_date = None
        date_str = item.get("publishedDate") or item.get("depositedDate")
        if date_str:
            try:
                pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        # DOI
        doi = None
        for ident in item.get("identifiers", []):
            if ident.startswith("doi:"):
                doi = ident[4:]
                break
        
        # URLs
        download_url = item.get("downloadUrl")
        
        return PaperData(
            title=title,
            abstract=item.get("abstract"),
            authors=authors,
            source=self.source_name,
            source_id=str(item.get("id", "")),
            journal=item.get("publisher"),
            doi=doi,
            url=download_url or item.get("sourceFulltextUrls", [None])[0] if item.get("sourceFulltextUrls") else None,
            published_date=pub_date,
            is_peer_reviewed=True,
            is_preprint=False,
            raw_data={
                "language": item.get("language"),
                "yearPublished": item.get("yearPublished"),
            }
        )
