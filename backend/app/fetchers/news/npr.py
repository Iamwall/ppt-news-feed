"""NPR News API fetcher.

https://www.npr.org/api/index.php
No API key required for RSS.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class NPRFetcher(BaseNewsFetcher):
    """Fetcher for NPR News via RSS."""
    
    source_name = "npr"
    category = "news"
    rate_limit = 2.0
    requires_api_key = False
    
    FEEDS = {
        "news": "https://feeds.npr.org/1001/rss.xml",
        "world": "https://feeds.npr.org/1004/rss.xml",
        "politics": "https://feeds.npr.org/1014/rss.xml",
        "business": "https://feeds.npr.org/1006/rss.xml",
        "technology": "https://feeds.npr.org/1019/rss.xml",
        "science": "https://feeds.npr.org/1007/rss.xml",
        "health": "https://feeds.npr.org/1128/rss.xml",
    }
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch news from NPR RSS feeds."""
        await self._rate_limit()
        
        # Determine which feeds to use
        feed_keys = ["news"]
        if keywords:
            for kw in keywords:
                if kw.lower() in self.FEEDS:
                    feed_keys.append(kw.lower())
        
        async with httpx.AsyncClient() as client:
            for feed_key in feed_keys[:3]:
                feed_url = self.FEEDS.get(feed_key, self.FEEDS["news"])
                
                response = await client.get(feed_url, timeout=30.0)
                response.raise_for_status()
                
                feed = feedparser.parse(response.text)
                
                count = 0
                for entry in feed.entries:
                    if count >= max_results // len(feed_keys):
                        break
                    
                    title = entry.get("title", "")
                    if not title:
                        continue
                    
                    if keywords:
                        combined = (title + " " + entry.get("summary", "")).lower()
                        if not any(kw.lower() in combined for kw in keywords if kw.lower() not in self.FEEDS):
                            continue
                    
                    pub_date = None
                    if entry.get("published_parsed"):
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    
                    yield NewsData(
                        title=title,
                        summary=entry.get("summary"),
                        source=self.source_name,
                        source_id=entry.get("id", ""),
                        url=entry.get("link"),
                        published_date=pub_date,
                        author="NPR",
                        category=feed_key,
                        tags=["npr", feed_key],
                        raw_data={}
                    )
                    count += 1
