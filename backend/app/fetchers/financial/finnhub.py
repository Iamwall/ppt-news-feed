"""Finnhub API fetcher for market news.

https://finnhub.io/docs/api
Requires API key. Free tier: 60 API calls/minute.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class FinnhubFetcher(BaseNewsFetcher):
    """Fetcher for Finnhub market news."""
    
    source_name = "finnhub"
    category = "financial"
    rate_limit = 1.0  # 60 calls/min = 1/sec
    requires_api_key = True
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("FINNHUB_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_KEY environment variable or api_key parameter required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch market news from Finnhub.
        
        Keywords are interpreted as stock symbols for company news.
        If no keywords, fetches general market news.
        """
        await self._rate_limit()
        
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        to_date = datetime.now(timezone.utc)
        
        params = {
            "token": self.api_key,
        }
        
        async with httpx.AsyncClient() as client:
            if keywords:
                # Fetch company news for each symbol
                for symbol in keywords:
                    await self._rate_limit()
                    
                    params.update({
                        "symbol": symbol.upper(),
                        "from": from_date.strftime("%Y-%m-%d"),
                        "to": to_date.strftime("%Y-%m-%d"),
                    })
                    
                    try:
                        response = await client.get(
                            f"{self.BASE_URL}/company-news",
                            params=params,
                            timeout=30.0,
                        )
                        response.raise_for_status()
                        news_items = response.json()
                        
                        for item in news_items[:max_results // len(keywords)]:
                            async for news in self._parse_item(item, symbol):
                                yield news
                                
                    except Exception as e:
                        print(f"Error fetching Finnhub news for {symbol}: {e}")
                        continue
            else:
                # Fetch general market news
                params["category"] = "general"
                
                response = await client.get(
                    f"{self.BASE_URL}/news",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                news_items = response.json()
                
                for item in news_items[:max_results]:
                    async for news in self._parse_item(item):
                        yield news
    
    async def _parse_item(self, item: dict, symbol: Optional[str] = None) -> AsyncIterator[NewsData]:
        """Parse a single Finnhub news item."""
        title = item.get("headline")
        if not title:
            return
        
        # Parse timestamp
        pub_date = None
        timestamp = item.get("datetime")
        if timestamp:
            pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        tags = ["finance", "market"]
        if symbol:
            tags.append(symbol.upper())
        if item.get("category"):
            tags.append(item.get("category"))
        
        yield NewsData(
            title=title,
            summary=item.get("summary"),
            source=self.source_name,
            source_id=str(item.get("id", "")),
            url=item.get("url"),
            published_date=pub_date,
            author=item.get("source"),
            category=self.category,
            image_url=item.get("image"),
            tags=tags,
            raw_data={
                "symbol": symbol,
                "category": item.get("category"),
                "related": item.get("related", ""),
            }
        )
