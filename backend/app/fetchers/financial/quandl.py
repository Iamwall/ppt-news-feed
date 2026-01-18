"""Quandl / Nasdaq Data Link API fetcher.

https://data.nasdaq.com/
Requires API key.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class QuandlFetcher(BaseNewsFetcher):
    """Fetcher for Nasdaq Data Link (formerly Quandl)."""
    
    source_name = "quandl"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = True
    
    BASE_URL = "https://data.nasdaq.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("NASDAQ_DATA_KEY")
        if not self.api_key:
            raise ValueError("NASDAQ_DATA_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch datasets from Nasdaq Data Link."""
        await self._rate_limit()
        
        query = " ".join(keywords) if keywords else "stock"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/datasets",
                params={"api_key": self.api_key, "query": query, "per_page": min(max_results, 100)},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        for dataset in data.get("datasets", []):
            name = dataset.get("name")
            if not name:
                continue
            
            yield NewsData(
                title=f"Nasdaq Data: {name}",
                summary=dataset.get("description", "")[:500] if dataset.get("description") else None,
                source=self.source_name,
                source_id=dataset.get("dataset_code", ""),
                url=f"https://data.nasdaq.com/data/{dataset.get('database_code', '')}/{dataset.get('dataset_code', '')}",
                published_date=datetime.now(timezone.utc),
                author="Nasdaq",
                category=self.category,
                tags=["nasdaq", "quandl", "finance"],
                raw_data={"database_code": dataset.get("database_code")}
            )
