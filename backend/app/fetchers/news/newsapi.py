"""NewsAPI fetcher.

https://newsapi.org/
Requires API key. Free tier: 100 requests/day, 1 month old articles.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class NewsAPIFetcher(BaseNewsFetcher):
    """Fetcher for NewsAPI.org - comprehensive news aggregator."""
    
    source_name = "newsapi"
    category = "general"
    rate_limit = 1.0  # Conservative for free tier
    requires_api_key = True
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError("NEWSAPI_KEY environment variable or api_key parameter required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch news articles from NewsAPI.
        
        Uses /everything endpoint for keyword search,
        or /top-headlines for general news.
        """
        await self._rate_limit()
        
        # Calculate date range
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        headers = {"X-Api-Key": self.api_key}
        
        async with httpx.AsyncClient() as client:
            if keywords:
                # Use everything endpoint for search
                params = {
                    "q": " OR ".join(keywords),
                    "from": from_date.strftime("%Y-%m-%d"),
                    "sortBy": "publishedAt",
                    "pageSize": min(max_results, 100),  # API max is 100
                    "language": "en",
                }
                endpoint = f"{self.BASE_URL}/everything"
            else:
                # Use top headlines for general news
                params = {
                    "country": "us",
                    "pageSize": min(max_results, 100),
                }
                endpoint = f"{self.BASE_URL}/top-headlines"
            
            response = await client.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") != "ok":
            raise ValueError(f"NewsAPI error: {data.get('message', 'Unknown error')}")
        
        articles = data.get("articles", [])
        
        for article in articles:
            title = article.get("title")
            if not title or title == "[Removed]":
                continue
            
            # Parse published date
            pub_date = None
            pub_str = article.get("publishedAt")
            if pub_str:
                try:
                    pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            # Extract source name for ID
            source_info = article.get("source", {})
            source_id = f"{source_info.get('id', 'unknown')}_{hash(article.get('url', ''))}"
            
            yield NewsData(
                title=title,
                summary=article.get("description"),
                source=self.source_name,
                source_id=source_id,
                url=article.get("url"),
                published_date=pub_date,
                author=article.get("author"),
                category=self.category,
                image_url=article.get("urlToImage"),
                tags=[source_info.get("name", "unknown")],
                raw_data={
                    "content": article.get("content"),
                    "source_name": source_info.get("name"),
                }
            )
