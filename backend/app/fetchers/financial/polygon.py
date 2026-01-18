"""Polygon.io API fetcher for market data.

https://polygon.io/docs/
Requires API key. Free tier: 5 calls/minute.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class PolygonFetcher(BaseNewsFetcher):
    """Fetcher for Polygon.io market news."""
    
    source_name = "polygon"
    category = "financial"
    rate_limit = 0.2  # 5 calls/minute
    requires_api_key = True
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("POLYGON_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch market news from Polygon.io."""
        await self._rate_limit()
        
        params = {
            "apiKey": self.api_key,
            "limit": min(max_results, 100),
            "order": "desc",
            "sort": "published_utc",
        }
        
        if keywords:
            params["ticker"] = ",".join(keywords[:5])
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/v2/reference/news",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        articles = data.get("results", [])
        
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            if article.get("published_utc"):
                try:
                    pub_date = datetime.fromisoformat(article["published_utc"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            tickers = article.get("tickers", [])
            
            yield NewsData(
                title=title,
                summary=article.get("description"),
                source=self.source_name,
                source_id=article.get("id", ""),
                url=article.get("article_url"),
                published_date=pub_date,
                author=article.get("author"),
                category=self.category,
                image_url=article.get("image_url"),
                tags=["finance"] + tickers[:5],
                raw_data={
                    "tickers": tickers,
                    "publisher": article.get("publisher", {}),
                }
            )
