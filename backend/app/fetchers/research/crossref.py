"""Crossref API fetcher for scholarly metadata.

https://www.crossref.org/documentation/retrieve-metadata/rest-api/
No API key required. Rate limit: 50 requests/second.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class CrossrefFetcher(BaseFetcher):
    """Fetcher for Crossref - the backbone of scholarly metadata."""
    
    source_name = "crossref"
    rate_limit = 10.0  # Conservative
    
    BASE_URL = "https://api.crossref.org"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch works from Crossref."""
        await self._rate_limit()
        
        # Build query
        params = {
            "rows": min(max_results, 1000),
            "sort": "published",
            "order": "desc",
        }
        
        if keywords:
            params["query"] = " ".join(keywords)
        
        # Add date filter
        from datetime import timedelta
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        params["filter"] = f"from-pub-date:{from_date.strftime('%Y-%m-%d')}"
        
        headers = {
            "User-Agent": "PPT-NewsFeed/1.0 (mailto:contact@example.com)"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/works",
                params=params,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        items = data.get("message", {}).get("items", [])
        
        for item in items:
            try:
                paper = self._parse_item(item)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing Crossref item: {e}")
                continue
    
    def _parse_item(self, item: dict) -> Optional[PaperData]:
        """Parse a Crossref work item."""
        # Get title (usually an array)
        titles = item.get("title", [])
        title = titles[0] if titles else None
        if not title:
            return None
        
        # DOI
        doi = item.get("DOI")
        
        # Authors
        authors = []
        for author in item.get("author", [])[:10]:
            given = author.get("given", "")
            family = author.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                affil = author.get("affiliation", [])
                affiliation = affil[0].get("name") if affil else None
                authors.append(AuthorData(name=name, affiliation=affiliation))
        
        # Publication date
        pub_date = None
        date_parts = item.get("published", {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            try:
                year = parts[0]
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                pub_date = datetime(year, month, day, tzinfo=timezone.utc)
            except (ValueError, IndexError):
                pass
        
        # Abstract
        abstract = item.get("abstract")
        if abstract:
            # Remove HTML tags
            import re
            abstract = re.sub(r'<[^>]+>', '', abstract)
        
        # Journal/container
        container = item.get("container-title", [])
        journal = container[0] if container else None
        
        # Type
        work_type = item.get("type", "")
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=doi or item.get("URL", ""),
            journal=journal,
            doi=doi,
            url=item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
            published_date=pub_date,
            citations=item.get("is-referenced-by-count"),
            is_peer_reviewed="journal" in work_type.lower(),
            is_preprint="preprint" in work_type.lower() or "posted-content" in work_type.lower(),
            raw_data={
                "type": work_type,
                "publisher": item.get("publisher"),
                "subject": item.get("subject", []),
            }
        )
