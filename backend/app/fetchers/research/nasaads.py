"""NASA ADS API fetcher for astrophysics papers.

https://ui.adsabs.harvard.edu/help/api/
Requires API key. 5000 queries/day.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class NASAADSFetcher(BaseFetcher):
    """Fetcher for NASA Astrophysics Data System."""
    
    source_name = "nasaads"
    rate_limit = 5.0
    
    BASE_URL = "https://api.adsabs.harvard.edu/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("NASA_ADS_KEY")
        if not self.api_key:
            raise ValueError("NASA_ADS_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from NASA ADS."""
        await self._rate_limit()
        
        # Build query
        query_parts = []
        if keywords:
            query_parts.append(" OR ".join(keywords))
        else:
            # Default to recent astronomy papers
            query_parts.append("astronomy")
        
        # Date filter
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        query_parts.append(f"pubdate:[{from_date.strftime('%Y-%m')} TO *]")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        params = {
            "q": " AND ".join(query_parts),
            "rows": min(max_results, 100),
            "sort": "date desc",
            "fl": "title,abstract,author,pubdate,doi,identifier,pub,citation_count,bibcode",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/query",
                params=params,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        docs = data.get("response", {}).get("docs", [])
        
        for doc in docs:
            try:
                paper = self._parse_doc(doc)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing NASA ADS doc: {e}")
                continue
    
    def _parse_doc(self, doc: dict) -> Optional[PaperData]:
        """Parse a single ADS document."""
        titles = doc.get("title", [])
        title = titles[0] if titles else None
        if not title:
            return None
        
        # Authors
        authors = []
        for name in doc.get("author", [])[:10]:
            authors.append(AuthorData(name=name))
        
        # Abstract
        abstracts = doc.get("abstract", [])
        abstract = abstracts[0] if abstracts else None
        
        # Publication date
        pub_date = None
        pubdate_str = doc.get("pubdate")
        if pubdate_str:
            try:
                # Format: YYYY-MM-00 or YYYY-MM
                parts = pubdate_str.split("-")
                year = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 and parts[1] != "00" else 1
                pub_date = datetime(year, month, 1, tzinfo=timezone.utc)
            except (ValueError, IndexError):
                pass
        
        # Bibcode is the unique identifier
        bibcode = doc.get("bibcode", "")
        
        # DOI
        doi = doc.get("doi", [None])[0] if doc.get("doi") else None
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=bibcode,
            journal=doc.get("pub"),
            doi=doi,
            url=f"https://ui.adsabs.harvard.edu/abs/{bibcode}" if bibcode else None,
            published_date=pub_date,
            citations=doc.get("citation_count"),
            is_peer_reviewed=True,
            is_preprint=False,
            raw_data={
                "bibcode": bibcode,
            }
        )
