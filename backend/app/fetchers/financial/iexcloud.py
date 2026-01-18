"""IEX Cloud API fetcher for market data.

https://iexcloud.io/docs/
Requires API key. Free tier available.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class IEXCloudFetcher(BaseNewsFetcher):
    """Fetcher for IEX Cloud market news."""
    
    source_name = "iexcloud"
    category = "financial"
    rate_limit = 5.0
    requires_api_key = True
    
    BASE_URL = "https://cloud.iexapis.com/stable"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("IEX_CLOUD_KEY")
        if not self.api_key:
            raise ValueError("IEX_CLOUD_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch market news from IEX Cloud.
        
        Keywords are interpreted as stock symbols.
        """
        await self._rate_limit()
        
        symbols = keywords if keywords else ["AAPL", "MSFT", "GOOGL", "AMZN"]
        
        async with httpx.AsyncClient() as client:
            for symbol in symbols[:10]:
                await self._rate_limit()
                
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/stock/{symbol}/news/last/5",
                        params={"token": self.api_key},
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    articles = response.json()
                    
                    for article in articles:
                        title = article.get("headline")
                        if not title:
                            continue
                        
                        # Parse timestamp
                        pub_date = None
                        if article.get("datetime"):
                            pub_date = datetime.fromtimestamp(
                                article.get("datetime") / 1000, 
                                tz=timezone.utc
                            )
                        
                        yield NewsData(
                            title=title,
                            summary=article.get("summary"),
                            source=self.source_name,
                            source_id=article.get("url", ""),
                            url=article.get("url"),
                            published_date=pub_date,
                            author=article.get("source"),
                            category=self.category,
                            image_url=article.get("image"),
                            tags=["finance", symbol.upper()],
                            raw_data={
                                "symbol": symbol,
                                "lang": article.get("lang"),
                                "hasPaywall": article.get("hasPaywall"),
                            }
                        )
                except Exception as e:
                    print(f"IEX Cloud error for {symbol}: {e}")
                    continue
