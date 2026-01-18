"""Bloomberg RSS fetcher.

No API key required for RSS.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class BloombergFetcher(BaseNewsFetcher):
    """Fetcher for Bloomberg financial news."""
    
    source_name = "bloomberg"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = False
    
    FEED_URL = "https://www.bloomberg.com/feed/podcast/top-news.xml"
    
    async def fetch(self, keywords=None, max_results=50, days_back=7) -> AsyncIterator[NewsData]:
        await self._rate_limit()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.FEED_URL, timeout=30.0)
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "")
            if not title or (keywords and not any(kw.lower() in title.lower() for kw in keywords)):
                continue
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if entry.get("published_parsed") else None
            yield NewsData(title=title, summary=entry.get("summary", "")[:500], source=self.source_name, source_id=entry.get("id", ""), url=entry.get("link"), published_date=pub_date, category=self.category, tags=["bloomberg", "finance"], raw_data={})
