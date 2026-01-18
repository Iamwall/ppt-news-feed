"""Google News RSS fetcher.

No API key required - uses public RSS feeds.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser
from urllib.parse import quote

from app.fetchers.base import BaseNewsFetcher, NewsData


class GoogleNewsFetcher(BaseNewsFetcher):
    """Fetcher for Google News via RSS."""
    
    source_name = "googlenews"
    category = "news"
    rate_limit = 1.0
    requires_api_key = False
    
    BASE_URL = "https://news.google.com/rss"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch news from Google News RSS."""
        await self._rate_limit()
        
        if keywords:
            url = f"{self.BASE_URL}/search?q={quote(' '.join(keywords))}&hl=en-US&gl=US&ceid=US:en"
        else:
            url = f"{self.BASE_URL}?hl=en-US&gl=US&ceid=US:en"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        count = 0
        for entry in feed.entries:
            if count >= max_results:
                break
            
            title = entry.get("title", "")
            if not title:
                continue
            
            pub_date = None
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            # Extract source from title
            source_name = None
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source_name = parts[1] if len(parts) > 1 else None
            
            yield NewsData(
                title=title,
                summary=entry.get("summary"),
                source=self.source_name,
                source_id=entry.get("id", entry.get("link", "")),
                url=entry.get("link"),
                published_date=pub_date,
                author=source_name,
                category=self.category,
                tags=["google", "news"],
                raw_data={}
            )
            count += 1
