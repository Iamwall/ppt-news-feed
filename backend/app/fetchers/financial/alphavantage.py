"""Alpha Vantage API fetcher for stock news and sentiment.

https://www.alphavantage.co/documentation/
Requires API key. Free tier: 25 calls/day.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class AlphaVantageFetcher(BaseNewsFetcher):
    """Fetcher for Alpha Vantage news and sentiment data."""
    
    source_name = "alphavantage"
    category = "financial"
    rate_limit = 0.2  # Very conservative - 25/day
    requires_api_key = True
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_KEY")
        if not self.api_key:
            raise ValueError("ALPHAVANTAGE_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch market news and sentiment from Alpha Vantage.
        
        Keywords are interpreted as stock tickers.
        """
        await self._rate_limit()
        
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "limit": min(max_results, 200),
        }
        
        if keywords:
            # Join tickers
            params["tickers"] = ",".join(keywords[:5])
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        if "Error Message" in data or "Note" in data:
            print(f"Alpha Vantage error: {data.get('Error Message') or data.get('Note')}")
            return
        
        articles = data.get("feed", [])
        
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            
            # Parse time
            pub_date = None
            time_str = article.get("time_published")
            if time_str:
                try:
                    pub_date = datetime.strptime(time_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            # Sentiment
            sentiment = article.get("overall_sentiment_score", 0)
            
            # Tickers mentioned
            tickers = [t.get("ticker") for t in article.get("ticker_sentiment", [])]
            
            yield NewsData(
                title=title,
                summary=article.get("summary"),
                source=self.source_name,
                source_id=article.get("url", ""),
                url=article.get("url"),
                published_date=pub_date,
                author=", ".join(article.get("authors", [])) or None,
                category=self.category,
                sentiment_score=sentiment,
                image_url=article.get("banner_image"),
                tags=["finance"] + tickers[:5],
                raw_data={
                    "overall_sentiment_label": article.get("overall_sentiment_label"),
                    "tickers": tickers,
                    "topics": [t.get("topic") for t in article.get("topics", [])],
                }
            )
