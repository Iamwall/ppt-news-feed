"""MedlinePlus Connect API fetcher.

https://medlineplus.gov/connect/overview.html
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class MedlinePlusFetcher(BaseNewsFetcher):
    """Fetcher for MedlinePlus health information."""
    
    source_name = "medlineplus"
    category = "health"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://connect.medlineplus.gov/service"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch health topics from MedlinePlus."""
        await self._rate_limit()
        
        if not keywords:
            keywords = ["diabetes", "heart disease", "cancer", "covid"]
        
        async with httpx.AsyncClient() as client:
            for keyword in keywords[:10]:
                await self._rate_limit()
                
                try:
                    response = await client.get(
                        self.BASE_URL,
                        params={
                            "mainSearchCriteria.v.c": keyword,
                            "knowledgeResponseType": "application/json",
                        },
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    feed = data.get("feed", {})
                    entries = feed.get("entry", [])
                    
                    for entry in entries[:max_results // len(keywords)]:
                        title = entry.get("title", {}).get("_value", "")
                        if not title:
                            continue
                        
                        summary = entry.get("summary", {}).get("_value", "")
                        links = entry.get("link", [])
                        url = links[0].get("href") if links else None
                        
                        yield NewsData(
                            title=title,
                            summary=summary[:500] if summary else None,
                            source=self.source_name,
                            source_id=entry.get("id", {}).get("_value", ""),
                            url=url,
                            published_date=datetime.now(timezone.utc),
                            author="MedlinePlus",
                            category=self.category,
                            tags=["medlineplus", "health", keyword],
                            raw_data={}
                        )
                except Exception as e:
                    print(f"MedlinePlus error for {keyword}: {e}")
                    continue
