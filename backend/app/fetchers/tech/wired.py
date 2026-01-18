"""Wired RSS fetcher.

No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class WiredFetcher(BaseNewsFetcher):
    """Fetcher for Wired via RSS."""
    
    source_name = "wired"
    category = "tech"
    rate_limit = 2.0
    requires_api_key = False
    
    FEED_URL = "https://www.wired.com/feed/rss"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch articles from Wired RSS."""
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
            
            yield NewsData(
                title=title,
                summary=entry.get("summary", "")[:500] if entry.get("summary") else None,
                source=self.source_name,
                source_id=entry.get("id", ""),
                url=entry.get("link"),
                published_date=pub_date,
                category=self.category,
                tags=["wired", "tech"],
                raw_data={}
            )
            count += 1
