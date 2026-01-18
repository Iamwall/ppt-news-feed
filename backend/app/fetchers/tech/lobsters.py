"""Lobste.rs API fetcher for tech news.

https://lobste.rs/about
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class LobstersFetcher(BaseNewsFetcher):
    """Fetcher for Lobste.rs tech community."""
    
    source_name = "lobsters"
    category = "tech"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://lobste.rs"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch stories from Lobste.rs."""
        await self._rate_limit()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/hottest.json",
                timeout=30.0,
            )
            response.raise_for_status()
            stories = response.json()
        
        count = 0
        for story in stories:
            if count >= max_results:
                break
            
            title = story.get("title", "")
            if not title:
                continue
            
            # Filter by keywords
            if keywords:
                combined = (title + " " + " ".join(story.get("tags", []))).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            # Parse date
            pub_date = None
            if story.get("created_at"):
                try:
                    pub_date = datetime.fromisoformat(story["created_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            tags = story.get("tags", [])
            
            yield NewsData(
                title=title,
                summary=story.get("description"),
                source=self.source_name,
                source_id=story.get("short_id", ""),
                url=story.get("url") or story.get("short_id_url"),
                published_date=pub_date,
                author=story.get("submitter_user", {}).get("username"),
                category=self.category,
                tags=["lobsters"] + tags[:5],
                raw_data={
                    "score": story.get("score"),
                    "comment_count": story.get("comment_count"),
                }
            )
            count += 1
