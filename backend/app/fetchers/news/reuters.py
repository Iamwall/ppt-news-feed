"""Reuters RSS fetcher.

No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class ReutersFetcher(BaseNewsFetcher):
    """Fetcher for Reuters via RSS."""
    
    source_name = "reuters"
    category = "news"
    rate_limit = 2.0
    requires_api_key = False
    
    FEEDS = {
        "world": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "business": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
        "tech": "https://www.reutersagency.com/feed/?best-topics=tech&post_type=best",
    }
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch articles from Reuters RSS."""
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
                            author="Reuters",
                            category=feed_name,
                            tags=["reuters", "news", feed_name],
                            raw_data={}
                        )
                        count += 1
                except Exception:
                    continue
