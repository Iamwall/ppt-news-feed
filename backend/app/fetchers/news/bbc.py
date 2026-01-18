"""BBC News RSS fetcher.

No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseNewsFetcher, NewsData


class BBCFetcher(BaseNewsFetcher):
    """Fetcher for BBC News via RSS."""
    
    source_name = "bbc"
    category = "news"
    rate_limit = 2.0
    requires_api_key = False
    
    FEEDS = {
        "world": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "science": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "business": "http://feeds.bbci.co.uk/news/business/rss.xml",
        "health": "http://feeds.bbci.co.uk/news/health/rss.xml",
    }
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch articles from BBC News RSS."""
        await self._rate_limit()
        
        # Select feeds based on keywords
        feeds_to_use = ["world", "technology"]
        if keywords:
            for kw in keywords:
                if kw.lower() in self.FEEDS:
                    feeds_to_use.append(kw.lower())
        
        async with httpx.AsyncClient() as client:
            for feed_name in list(set(feeds_to_use))[:3]:
                feed_url = self.FEEDS.get(feed_name, self.FEEDS["world"])
                
                try:
                    response = await client.get(feed_url, timeout=30.0)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.text)
                    
                    count = 0
                    for entry in feed.entries:
                        if count >= max_results // len(feeds_to_use):
                            break
                        
                        title = entry.get("title", "")
                        if not title:
                            continue
                        
                        if keywords:
                            combined = (title + " " + entry.get("summary", "")).lower()
                            kw_filter = [kw for kw in keywords if kw.lower() not in self.FEEDS]
                            if kw_filter and not any(kw.lower() in combined for kw in kw_filter):
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
                            author="BBC",
                            category=feed_name,
                            tags=["bbc", "news", feed_name],
                            raw_data={}
                        )
                        count += 1
                except Exception:
                    continue
