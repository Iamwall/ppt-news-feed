"""FRED (Federal Reserve Economic Data) API fetcher.

https://fred.stlouisfed.org/docs/api/
Requires API key. Free.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class FREDFetcher(BaseNewsFetcher):
    """Fetcher for FRED economic data releases and news."""
    
    source_name = "fred"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = True
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("FRED_KEY")
        if not self.api_key:
            raise ValueError("FRED_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch recent economic data releases from FRED.
        
        Keywords filter by series tag (e.g., 'gdp', 'inflation', 'unemployment').
        """
        await self._rate_limit()
        
        # Get recently updated series
        params = {
            "api_key": self.api_key,
            "file_type": "json",
            "limit": min(max_results, 100),
            "order_by": "popularity",
            "sort_order": "desc",
        }
        
        if keywords:
            params["tag_names"] = ";".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/tags/series",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        series_list = data.get("seriess", [])
        
        for series in series_list:
            title = series.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            date_str = series.get("last_updated")
            if date_str:
                try:
                    pub_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            series_id = series.get("id", "")
            
            yield NewsData(
                title=f"FRED: {title}",
                summary=series.get("notes", "")[:500] if series.get("notes") else None,
                source=self.source_name,
                source_id=series_id,
                url=f"https://fred.stlouisfed.org/series/{series_id}",
                published_date=pub_date,
                author="Federal Reserve",
                category=self.category,
                tags=["economics", "federal-reserve", series.get("frequency", "").lower()],
                raw_data={
                    "frequency": series.get("frequency"),
                    "units": series.get("units"),
                    "seasonal_adjustment": series.get("seasonal_adjustment"),
                    "popularity": series.get("popularity"),
                }
            )
