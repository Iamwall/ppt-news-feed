"""Haxor wrapper for Hacker News (alternative implementation).

https://github.com/avinassh/haxor
Provides more features than basic HN API.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import asyncio

from app.fetchers.base import BaseNewsFetcher, NewsData


class HaxorFetcher(BaseNewsFetcher):
    """Alternative Hacker News fetcher using different endpoints."""
    
    source_name = "haxor"
    category = "tech"
    rate_limit = 1.0
    requires_api_key = False
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch Ask HN, Show HN, and jobs from Hacker News."""
        import httpx
        
        await self._rate_limit()
        
        # Get different story types
        story_types = ["askstories", "showstories", "jobstories"]
        
        async with httpx.AsyncClient() as client:
            for story_type in story_types:
                await self._rate_limit()
                
                response = await client.get(
                    f"{self.BASE_URL}/{story_type}.json",
                    timeout=30.0,
                )
                response.raise_for_status()
                story_ids = response.json()
                
                # Fetch story details
                for story_id in story_ids[:max_results // len(story_types)]:
                    await self._rate_limit()
                    
                    try:
                        response = await client.get(
                            f"{self.BASE_URL}/item/{story_id}.json",
                            timeout=10.0,
                        )
                        response.raise_for_status()
                        story = response.json()
                        
                        if not story:
                            continue
                        
                        title = story.get("title", "")
                        if not title:
                            continue
                        
                        # Filter by keywords
                        if keywords:
                            combined = (title + " " + story.get("text", "")).lower()
                            if not any(kw.lower() in combined for kw in keywords):
                                continue
                        
                        # Parse timestamp
                        pub_date = None
                        if story.get("time"):
                            pub_date = datetime.fromtimestamp(story["time"], tz=timezone.utc)
                        
                        yield NewsData(
                            title=title,
                            summary=story.get("text", "")[:500] if story.get("text") else None,
                            source=self.source_name,
                            source_id=str(story_id),
                            url=story.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                            published_date=pub_date,
                            author=story.get("by"),
                            category=self.category,
                            tags=["hackernews", story_type.replace("stories", "")],
                            raw_data={
                                "score": story.get("score"),
                                "descendants": story.get("descendants"),
                                "type": story.get("type"),
                            }
                        )
                    except Exception as e:
                        print(f"Haxor story fetch error: {e}")
                        continue
