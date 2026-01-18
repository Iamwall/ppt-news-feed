"""PhilPapers API fetcher for philosophy research.

https://philpapers.org/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class PhilPapersFetcher(BaseFetcher):
    """Fetcher for PhilPapers philosophy database."""
    
    source_name = "philpapers"
    rate_limit = 1.0
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from PhilPapers RSS."""
        await self._rate_limit()
        
        import feedparser
        
        # Use RSS feed
        feed_url = "https://philpapers.org/recent.atom"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(feed_url, timeout=30.0)
            response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        count = 0
        for entry in feed.entries:
            if count >= max_results:
                break
            
            title = entry.get("title", "")
            if not title:
                continue
            
            # Filter by keywords
            if keywords:
                combined = (title + " " + entry.get("summary", "")).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            # Parse date
            pub_date = None
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            # Parse authors
            authors = []
            for author in entry.get("authors", [])[:5]:
                name = author.get("name")
                if name:
                    authors.append(AuthorData(name=name))
            
            yield PaperData(
                title=title,
                abstract=entry.get("summary", "")[:2000] if entry.get("summary") else None,
                authors=authors,
                source=self.source_name,
                source_id=entry.get("id", ""),
                url=entry.get("link"),
                published_date=pub_date,
                is_peer_reviewed=True,
                is_preprint=False,
                raw_data={
                    "categories": [t.get("term") for t in entry.get("tags", [])],
                }
            )
            count += 1
