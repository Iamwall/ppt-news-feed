"""Bing News Search API fetcher.

https://docs.microsoft.com/en-us/azure/cognitive-services/bing-news-search/
Requires Azure API key.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class BingNewsFetcher(BaseNewsFetcher):
    """Fetcher for Bing News Search API."""
    
    source_name = "bingnews"
    category = "news"
    rate_limit = 3.0
    requires_api_key = True
    
    BASE_URL = "https://api.bing.microsoft.com/v7.0/news/search"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("BING_NEWS_KEY")
        if not self.api_key:
            raise ValueError("BING_NEWS_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch news from Bing News."""
        await self._rate_limit()
        
        query = " ".join(keywords) if keywords else "technology"
        
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": min(max_results, 100), "freshness": "Week", "mkt": "en-US"}
        
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(self.BASE_URL, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        
        for article in data.get("value", []):
            title = article.get("name")
            if not title:
                continue
            
            pub_date = None
            if article.get("datePublished"):
                try:
                    pub_date = datetime.fromisoformat(article["datePublished"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            yield NewsData(
                title=title,
                summary=article.get("description"),
                source=self.source_name,
                source_id=article.get("url", ""),
                url=article.get("url"),
                published_date=pub_date,
                author=article.get("provider", [{}])[0].get("name") if article.get("provider") else None,
                category=self.category,
                image_url=article.get("image", {}).get("thumbnail", {}).get("contentUrl") if article.get("image") else None,
                tags=["bing", "news"],
                raw_data={}
            )
