"""WHO GHO OData API fetcher for global health statistics.

https://www.who.int/data/gho/info/gho-odata-api
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class WHOFetcher(BaseNewsFetcher):
    """Fetcher for WHO Global Health Observatory data."""
    
    source_name = "who"
    category = "health"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://ghoapi.azureedge.net/api"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch health indicators and data from WHO."""
        await self._rate_limit()
        
        # Get indicators (health metrics)
        async with httpx.AsyncClient() as client:
            # First get list of indicators
            response = await client.get(
                f"{self.BASE_URL}/Indicator",
                params={"$top": max_results},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        indicators = data.get("value", [])
        
        for ind in indicators:
            code = ind.get("IndicatorCode", "")
            name = ind.get("IndicatorName", "")
            
            if not name:
                continue
            
            # Filter by keywords
            if keywords:
                combined = (name + " " + code).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            yield NewsData(
                title=f"WHO: {name}",
                summary=ind.get("Definition"),
                source=self.source_name,
                source_id=code,
                url=f"https://www.who.int/data/gho/data/indicators/indicator-details/GHO/{code}",
                published_date=datetime.now(timezone.utc),
                author="World Health Organization",
                category=self.category,
                tags=["who", "health", "global"],
                raw_data={
                    "indicator_code": code,
                    "language": ind.get("Language"),
                }
            )
