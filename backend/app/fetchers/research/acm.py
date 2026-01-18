"""ACM Digital Library fetcher.

https://dl.acm.org/
Uses RSS feed - no API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class ACMFetcher(BaseFetcher):
    """Fetcher for ACM Digital Library via RSS."""
    
    source_name = "acm"
    rate_limit = 2.0
    
    FEED_URL = "https://dl.acm.org/action/showFeed?type=etoc&feed=rss&jc=cacm"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from ACM via RSS."""
        await self._rate_limit()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.FEED_URL, timeout=30.0)
            response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        count = 0
        for entry in feed.entries:
            if count >= max_results:
                break
            
            title = entry.get("title", "")
            if not title:
                continue
            
            if keywords:
                combined = (title + " " + entry.get("summary", "")).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            pub_date = None
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            authors = []
            for author in entry.get("authors", [])[:10]:
                if author.get("name"):
                    authors.append(AuthorData(name=author["name"]))
            
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
                raw_data={}
            )
            count += 1
