"""CryptoCompare API fetcher.

https://min-api.cryptocompare.com/documentation
Free tier available.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class CryptoCompareFetcher(BaseNewsFetcher):
    """Fetcher for CryptoCompare crypto news."""
    
    source_name = "cryptocompare"
    category = "financial"
    rate_limit = 5.0
    requires_api_key = False  # Has free tier
    
    BASE_URL = "https://min-api.cryptocompare.com/data/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("CRYPTOCOMPARE_KEY")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch crypto news from CryptoCompare."""
        await self._rate_limit()
        
        headers = {}
        if self.api_key:
            headers["authorization"] = f"Apikey {self.api_key}"
        
        params = {
            "lang": "EN",
        }
        
        if keywords:
            params["categories"] = ",".join(keywords[:5])
        
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(
                f"{self.BASE_URL}/news/",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        articles = data.get("Data", [])
        
        for article in articles[:max_results]:
            title = article.get("title")
            if not title:
                continue
            
            # Parse timestamp
            pub_date = None
            if article.get("published_on"):
                pub_date = datetime.fromtimestamp(article["published_on"], tz=timezone.utc)
            
            yield NewsData(
                title=title,
                summary=article.get("body", "")[:500] if article.get("body") else None,
                source=self.source_name,
                source_id=str(article.get("id", "")),
                url=article.get("url"),
                published_date=pub_date,
                author=article.get("source"),
                category=self.category,
                image_url=article.get("imageurl"),
                tags=["crypto"] + article.get("categories", "").split("|")[:5],
                raw_data={
                    "source_info": article.get("source_info"),
                }
            )
