"""DrugBank data fetcher.

https://go.drugbank.com/
Requires API key for full access.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class DrugBankFetcher(BaseNewsFetcher):
    """Fetcher for DrugBank drug information."""
    
    source_name = "drugbank"
    category = "health"
    rate_limit = 1.0
    requires_api_key = True
    
    BASE_URL = "https://go.drugbank.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("DRUGBANK_KEY")
        if not self.api_key:
            raise ValueError("DRUGBANK_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch drug data from DrugBank."""
        await self._rate_limit()
        
        query = keywords[0] if keywords else "aspirin"
        
        headers = {"Authorization": self.api_key}
        
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(
                f"{self.BASE_URL}/drugs",
                params={"q": query, "page_size": min(max_results, 50)},
                timeout=30.0,
            )
            response.raise_for_status()
            drugs = response.json()
        
        for drug in drugs:
            name = drug.get("name")
            if not name:
                continue
            
            yield NewsData(
                title=f"DrugBank: {name}",
                summary=drug.get("description", "")[:500] if drug.get("description") else None,
                source=self.source_name,
                source_id=drug.get("drugbank_id", ""),
                url=f"https://go.drugbank.com/drugs/{drug.get('drugbank_id', '')}",
                published_date=datetime.now(timezone.utc),
                author="DrugBank",
                category=self.category,
                tags=["drugbank", "pharmaceutical", "drug"],
                raw_data={"cas_number": drug.get("cas_number")}
            )
