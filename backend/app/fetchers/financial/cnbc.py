"""CNBC RSS fetcher."""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx, feedparser
from app.fetchers.base import BaseNewsFetcher, NewsData

class CNBCFetcher(BaseNewsFetcher):
    source_name = "cnbc"
    category = "financial"
    rate_limit = 2.0
    FEED_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    
    async def fetch(self, keywords=None, max_results=50, days_back=7) -> AsyncIterator[NewsData]:
        await self._rate_limit()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.FEED_URL, timeout=30.0)
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "")
            if not title: continue
            if keywords and not any(kw.lower() in title.lower() for kw in keywords): continue
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if entry.get("published_parsed") else None
            yield NewsData(title=title, summary=entry.get("summary", "")[:500], source=self.source_name, source_id=entry.get("id", ""), url=entry.get("link"), published_date=pub_date, category=self.category, tags=["cnbc", "finance"], raw_data={})
