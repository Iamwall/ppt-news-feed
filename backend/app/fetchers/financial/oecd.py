"""OECD Data API fetcher.

https://data.oecd.org/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class OECDFetcher(BaseNewsFetcher):
    """Fetcher for OECD economic data."""
    
    source_name = "oecd"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://stats.oecd.org/SDMX-JSON/data"
    
    DATASETS = ["GDP", "CPI", "UNEMP", "STLABOUR"]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch economic data from OECD."""
        await self._rate_limit()
        
        datasets = keywords if keywords else self.DATASETS
        
        async with httpx.AsyncClient() as client:
            for dataset in datasets[:5]:
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/{dataset.upper()}/all/all",
                        params={"lastNObservations": 1},
                        timeout=30.0,
                    )
                    
                    if response.status_code != 200:
                        continue
                    
                    yield NewsData(
                        title=f"OECD: {dataset.upper()} Data",
                        summary=f"Latest {dataset.upper()} data from OECD",
                        source=self.source_name,
                        source_id=dataset.upper(),
                        url=f"https://data.oecd.org/{dataset.lower()}",
                        published_date=datetime.now(timezone.utc),
                        author="OECD",
                        category=self.category,
                        tags=["oecd", "economics", dataset.lower()],
                        raw_data={}
                    )
                except Exception:
                    continue
