"""Dev.to API fetcher.

https://developers.forem.com/api
No API key required for reading. Rate limit: ~60 requests/min.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class DevToFetcher(BaseNewsFetcher):
    """Fetcher for Dev.to developer community articles."""
    
    source_name = "devto"
    category = "tech"
    rate_limit = 1.0
    requires_api_key = False
    
    BASE_URL = "https://dev.to/api"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch articles from Dev.to."""
        await self._rate_limit()
        
        params = {
            "per_page": min(max_results, 100),
            "top": days_back,  # Articles from top of last N days
        }
        
        # If keywords provided, use as tags or search
        if keywords:
            # Dev.to supports tag filtering
            # Try first keyword as tag
            params["tag"] = keywords[0].lower().replace(" ", "")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/articles",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            articles = response.json()
        
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            
            # Filter by additional keywords if provided
            if keywords and len(keywords) > 1:
                combined = f"{title} {article.get('description', '')}".lower()
                if not any(kw.lower() in combined for kw in keywords[1:]):
                    continue
            
            # Parse published date
            pub_date = None
            pub_str = article.get("published_at")
            if pub_str:
                try:
                    pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            # Get tags
            tags = article.get("tag_list", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            
            yield NewsData(
                title=title,
                summary=article.get("description"),
                source=self.source_name,
                source_id=str(article.get("id")),
                url=article.get("url"),
                published_date=pub_date,
                author=article.get("user", {}).get("name"),
                category=self.category,
                image_url=article.get("cover_image") or article.get("social_image"),
                tags=["devto"] + tags[:5],
                raw_data={
                    "reading_time_minutes": article.get("reading_time_minutes"),
                    "positive_reactions_count": article.get("positive_reactions_count"),
                    "comments_count": article.get("comments_count"),
                    "username": article.get("user", {}).get("username"),
                }
            )
