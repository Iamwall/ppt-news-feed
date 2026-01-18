"""OpenFDA API fetcher for drug/device safety news.

https://open.fda.gov/apis/
No API key required. Rate limit: 240 requests/minute without key, 120K/day with key.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class OpenFDAFetcher(BaseNewsFetcher):
    """Fetcher for OpenFDA drug safety and recall information."""
    
    source_name = "openfda"
    category = "health"
    rate_limit = 4.0  # 240/min = 4/sec
    requires_api_key = False
    
    BASE_URL = "https://api.fda.gov"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch drug safety events and recalls from OpenFDA.
        
        Fetches from multiple endpoints: drug events, device recalls, food recalls.
        """
        await self._rate_limit()
        
        # Calculate date range
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        from_date_str = from_date.strftime("%Y%m%d")
        
        # Endpoints to query
        endpoints = [
            ("/drug/enforcement.json", "drug_recall"),
            ("/device/recall.json", "device_recall"),
            ("/food/enforcement.json", "food_recall"),
        ]
        
        results_per_endpoint = max_results // len(endpoints) + 1
        
        async with httpx.AsyncClient() as client:
            for endpoint, event_type in endpoints:
                await self._rate_limit()
                
                try:
                    params = {
                        "limit": min(results_per_endpoint, 100),
                        "sort": "report_date:desc",
                    }
                    
                    # Build search query
                    search_parts = [f"report_date:[{from_date_str} TO *]"]
                    if keywords:
                        keyword_query = " AND ".join(f'"{kw}"' for kw in keywords)
                        search_parts.append(f"reason_for_recall:{keyword_query}")
                    
                    params["search"] = " AND ".join(search_parts)
                    
                    response = await client.get(
                        f"{self.BASE_URL}{endpoint}",
                        params=params,
                        timeout=30.0,
                    )
                    
                    if response.status_code == 404:
                        # No results for this query
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    results = data.get("results", [])
                    
                    for item in results:
                        async for news in self._parse_recall(item, event_type):
                            yield news
                            
                except Exception as e:
                    print(f"Error fetching OpenFDA {event_type}: {e}")
                    continue
    
    async def _parse_recall(self, item: dict, event_type: str) -> AsyncIterator[NewsData]:
        """Parse a single recall/event item."""
        # Build title from recall info
        product = item.get("product_description", "Unknown product")[:100]
        classification = item.get("classification", "")
        title = f"FDA {event_type.replace('_', ' ').title()}: {product}"
        if classification:
            title = f"[{classification}] {title}"
        
        # Parse date
        pub_date = None
        date_str = item.get("report_date") or item.get("recall_initiation_date")
        if date_str:
            try:
                pub_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        # Build summary
        reason = item.get("reason_for_recall", "")
        summary = reason[:500] if reason else None
        
        # Generate unique ID
        recall_id = item.get("recall_number") or item.get("event_id") or str(hash(title))
        
        yield NewsData(
            title=title,
            summary=summary,
            source=self.source_name,
            source_id=str(recall_id),
            url="https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
            published_date=pub_date,
            author="FDA",
            category=self.category,
            tags=["fda", "health", event_type, classification.lower() if classification else "recall"],
            raw_data={
                "classification": classification,
                "status": item.get("status"),
                "recalling_firm": item.get("recalling_firm"),
                "distribution_pattern": item.get("distribution_pattern"),
                "event_type": event_type,
            }
        )
