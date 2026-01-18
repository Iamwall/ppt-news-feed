"""World Bank Data API fetcher.

https://data.worldbank.org/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class WorldBankFetcher(BaseNewsFetcher):
    """Fetcher for World Bank economic indicators."""
    
    source_name = "worldbank"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch indicators from World Bank."""
        await self._rate_limit()
        
        # Get list of indicators
        params = {"format": "json", "per_page": min(max_results, 100)}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/indicator", params=params, timeout=60.0)
            response.raise_for_status()
            data = response.json()
        
        if len(data) < 2:
            return
        
        indicators = data[1] if isinstance(data, list) else []
        
        for ind in indicators:
            name = ind.get("name", "")
            if not name:
                continue
            
            if keywords:
                combined = (name + " " + ind.get("sourceNote", "")).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            yield NewsData(
                title=f"World Bank: {name}",
                summary=ind.get("sourceNote", "")[:500] if ind.get("sourceNote") else None,
                source=self.source_name,
                source_id=ind.get("id", ""),
                url=f"https://data.worldbank.org/indicator/{ind.get('id', '')}",
                published_date=datetime.now(timezone.utc),
                author="World Bank",
                category=self.category,
                tags=["worldbank", "economics", "indicator"],
                raw_data={"source": ind.get("source", {}).get("value")}
            )
