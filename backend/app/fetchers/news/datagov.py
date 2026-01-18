"""Data.gov API fetcher for US government data.

https://data.gov/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class DataGovFetcher(BaseNewsFetcher):
    """Fetcher for Data.gov US government datasets."""
    
    source_name = "datagov"
    category = "news"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://catalog.data.gov/api/3/action"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch datasets from Data.gov."""
        await self._rate_limit()
        
        params = {
            "rows": min(max_results, 100),
            "sort": "metadata_modified desc",
        }
        
        if keywords:
            params["q"] = " ".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/package_search",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        datasets = data.get("result", {}).get("results", [])
        
        for ds in datasets:
            title = ds.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            if ds.get("metadata_modified"):
                try:
                    pub_date = datetime.fromisoformat(ds["metadata_modified"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            org = ds.get("organization", {})
            
            yield NewsData(
                title=f"Data.gov: {title}",
                summary=ds.get("notes", "")[:500] if ds.get("notes") else None,
                source=self.source_name,
                source_id=ds.get("id", ""),
                url=f"https://catalog.data.gov/dataset/{ds.get('name', '')}",
                published_date=pub_date,
                author=org.get("title") if org else None,
                category=self.category,
                tags=["government", "data"] + [t.get("name") for t in ds.get("tags", [])[:5]],
                raw_data={
                    "organization": org.get("title") if org else None,
                    "num_resources": ds.get("num_resources"),
                }
            )
