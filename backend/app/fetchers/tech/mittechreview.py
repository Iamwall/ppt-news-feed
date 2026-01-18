"""MIT Technology Review RSS fetcher.

No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class MITTechReviewFetcher(BaseNewsFetcher):
    """Fetcher for MIT Technology Review."""
    
    source_name = "mittechreview"
    category = "tech"
    rate_limit = 2.0
    requires_api_key = False
    
    FEED_URL = "https://www.technologyreview.com/feed/"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch from MIT Technology Review RSS."""
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
            
            if keywords and not any(kw.lower() in (title + " " + entry.get("summary", "")).lower() for kw in keywords):
                continue
            
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if entry.get("published_parsed") else None
            
            yield NewsData(
                title=title,
                summary=entry.get("summary", "")[:500] if entry.get("summary") else None,
                source=self.source_name,
                source_id=entry.get("id", ""),
                url=entry.get("link"),
                published_date=pub_date,
                category=self.category,
                tags=["mit", "technology"],
                raw_data={}
            )
            count += 1
