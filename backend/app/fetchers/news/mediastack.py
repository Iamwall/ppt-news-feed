"""Mediastack API fetcher for live news.

https://mediastack.com/documentation
Requires API key. Free tier: 500 req/month.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class MediastackFetcher(BaseNewsFetcher):
    """Fetcher for Mediastack live news API."""
    
    source_name = "mediastack"
    category = "news"
    rate_limit = 0.5  # Conservative
    requires_api_key = True
    
    BASE_URL = "http://api.mediastack.com/v1/news"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("MEDIASTACK_KEY")
        if not self.api_key:
            raise ValueError("MEDIASTACK_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch news from Mediastack."""
        await self._rate_limit()
        
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        params = {
            "access_key": self.api_key,
            "limit": min(max_results, 100),
            "languages": "en",
            "sort": "published_desc",
            "date": f"{from_date.strftime('%Y-%m-%d')},{datetime.now().strftime('%Y-%m-%d')}",
        }
        
        if keywords:
            params["keywords"] = ",".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        if "error" in data:
            print(f"Mediastack error: {data['error']}")
            return
        
        articles = data.get("data", [])
        
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            date_str = article.get("published_at")
            if date_str:
                try:
                    pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            yield NewsData(
                title=title,
                summary=article.get("description"),
                source=self.source_name,
                source_id=article.get("url", ""),
                url=article.get("url"),
                published_date=pub_date,
                author=article.get("author"),
                category=article.get("category") or self.category,
                image_url=article.get("image"),
                tags=[article.get("category")] if article.get("category") else [],
                raw_data={
                    "source_name": article.get("source"),
                    "country": article.get("country"),
                    "language": article.get("language"),
                }
            )
