"""DBLP Computer Science Bibliography fetcher.

https://dblp.org/faq/How+to+use+the+dblp+search+API.html
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class DBLPFetcher(BaseFetcher):
    """Fetcher for DBLP computer science bibliography."""
    
    source_name = "dblp"
    rate_limit = 1.0
    
    BASE_URL = "https://dblp.org/search/publ/api"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from DBLP."""
        await self._rate_limit()
        
        query = " ".join(keywords) if keywords else "machine learning"
        
        params = {
            "q": query,
            "h": min(max_results, 100),
            "format": "json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=60.0)
            response.raise_for_status()
            data = response.json()
        
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        
        for hit in hits:
            info = hit.get("info", {})
            title = info.get("title")
            if not title:
                continue
            
            # Authors
            authors = []
            author_info = info.get("authors", {}).get("author", [])
            if isinstance(author_info, dict):
                author_info = [author_info]
            for a in author_info[:10]:
                name = a.get("text") if isinstance(a, dict) else a
                if name:
                    authors.append(AuthorData(name=name))
            
            # Parse year
            pub_date = None
            if info.get("year"):
                try:
                    pub_date = datetime(int(info["year"]), 1, 1, tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            yield PaperData(
                title=title,
                authors=authors,
                source=self.source_name,
                source_id=hit.get("@id", ""),
                journal=info.get("venue"),
                doi=info.get("doi"),
                url=info.get("ee") if isinstance(info.get("ee"), str) else (info.get("ee", [None])[0] if info.get("ee") else None),
                published_date=pub_date,
                is_peer_reviewed=True,
                is_preprint=False,
                raw_data={"type": info.get("type")}
            )
