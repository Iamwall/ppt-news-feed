"""MarketWatch RSS fetcher.

No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class MarketWatchFetcher(BaseNewsFetcher):
    """Fetcher for MarketWatch via RSS."""
    
    source_name = "marketwatch"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = False
    
    FEEDS = {
        "topstories": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "markets": "https://feeds.content.dowjones.io/public/rss/mw_bulletins",
        "technology": "https://feeds.content.dowjones.io/public/rss/mw_technology",
    }
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch articles from MarketWatch RSS."""
        await self._rate_limit()
        
        async with httpx.AsyncClient() as client:
            for feed_name, feed_url in self.FEEDS.items():
                try:
                    response = await client.get(feed_url, timeout=30.0)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.text)
                    
                    count = 0
                    for entry in feed.entries:
                        if count >= max_results // 3:
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
                            tags=["marketwatch", "finance", feed_name],
                            raw_data={}
                        )
                        count += 1
                except Exception:
                    continue
