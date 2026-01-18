"""CDC Data API fetcher.

https://data.cdc.gov/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class CDCFetcher(BaseNewsFetcher):
    """Fetcher for CDC public health data."""
    
    source_name = "cdc"
    category = "health"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://data.cdc.gov/api/views"
    
    # Popular CDC datasets
    DATASETS = [
        ("9mfq-cb36", "COVID-19 Vaccinations"),
        ("pwn4-m3yp", "COVID-19 Cases"),
        ("muzy-jte6", "Flu Surveillance"),
    ]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch public health data from CDC."""
        await self._rate_limit()
        
        async with httpx.AsyncClient() as client:
            for dataset_id, dataset_name in self.DATASETS:
                if keywords:
                    if not any(kw.lower() in dataset_name.lower() for kw in keywords):
                        continue
                
                await self._rate_limit()
                
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/{dataset_id}.json",
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    yield NewsData(
                        title=f"CDC: {data.get('name', dataset_name)}",
                        summary=data.get("description", "")[:500] if data.get("description") else None,
                        source=self.source_name,
                        source_id=dataset_id,
                        url=f"https://data.cdc.gov/d/{dataset_id}",
                        published_date=datetime.now(timezone.utc),
                        author="Centers for Disease Control",
                        category=self.category,
                        tags=["cdc", "health", "public-health"],
                        raw_data={
                            "dataset_id": dataset_id,
                            "category": data.get("category"),
                        }
                    )
                except Exception as e:
                    print(f"CDC fetch error for {dataset_id}: {e}")
                    continue
