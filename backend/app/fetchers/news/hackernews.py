"""Hacker News API fetcher.

Official HN API: https://github.com/HackerNews/API
No API key required. Rate limit: ~10 req/sec recommended.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class HackerNewsFetcher(BaseNewsFetcher):
    """Fetcher for Hacker News using the official Firebase API."""
    
    source_name = "hackernews"
    category = "tech"
    rate_limit = 5.0  # Conservative rate limit
    requires_api_key = False
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch top stories from Hacker News.
        
        Note: HN API doesn't support keyword search directly.
        We fetch top/new stories and filter by keywords if provided.
        """
        await self._rate_limit()
        
        # Get story IDs (top stories are most popular)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/topstories.json",
                timeout=30.0
            )
            response.raise_for_status()
            story_ids = response.json()
        
        # Limit to reasonable number to fetch
        story_ids = story_ids[:max_results * 2]  # Fetch extras for filtering
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        fetched = 0
        
        async with httpx.AsyncClient() as client:
            for story_id in story_ids:
                if fetched >= max_results:
                    break
                
                await self._rate_limit()
                
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/item/{story_id}.json",
                        timeout=10.0
                    )
                    response.raise_for_status()
                    item = response.json()
                    
                    if not item or item.get("type") != "story":
                        continue
                    
                    # Parse timestamp
                    timestamp = item.get("time")
                    pub_date = None
                    if timestamp:
                        pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        if pub_date < cutoff_date:
                            continue
                    
                    title = item.get("title", "")
                    
                    # Filter by keywords if provided
                    if keywords:
                        title_lower = title.lower()
                        text_lower = (item.get("text") or "").lower()
                        combined = title_lower + " " + text_lower
                        if not any(kw.lower() in combined for kw in keywords):
                            continue
                    
                    # Build URL (prefer external URL, fallback to HN discussion)
                    url = item.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
                    
                    news_item = NewsData(
                        title=title,
                        summary=item.get("text"),  # Text is available for Ask HN, etc.
                        source=self.source_name,
                        source_id=str(story_id),
                        url=url,
                        published_date=pub_date,
                        author=item.get("by"),
                        category=self.category,
                        tags=["hackernews", "tech"],
                        raw_data={
                            "score": item.get("score", 0),
                            "descendants": item.get("descendants", 0),  # comment count
                            "type": item.get("type"),
                        }
                    )
                    
                    fetched += 1
                    yield news_item
                    
                except Exception as e:
                    print(f"Error fetching HN story {story_id}: {e}")
                    continue
