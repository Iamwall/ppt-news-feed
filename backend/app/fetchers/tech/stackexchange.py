"""StackExchange API fetcher.

https://api.stackexchange.com/
No API key required (300 requests/day). With key: 10K/day.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx
import gzip
from io import BytesIO

from app.fetchers.base import BaseNewsFetcher, NewsData


class StackExchangeFetcher(BaseNewsFetcher):
    """Fetcher for StackExchange trending questions."""
    
    source_name = "stackexchange"
    category = "tech"
    rate_limit = 0.5  # Be conservative with rate limit
    requires_api_key = False
    
    BASE_URL = "https://api.stackexchange.com/2.3"
    
    # Default sites to query
    DEFAULT_SITES = ["stackoverflow", "serverfault", "superuser"]
    
    def __init__(self, sites: Optional[List[str]] = None):
        super().__init__()
        self.sites = sites or self.DEFAULT_SITES
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch trending questions from StackExchange sites.
        
        Keywords are used as tags to filter questions.
        """
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        from_timestamp = int(from_date.timestamp())
        
        results_per_site = max_results // len(self.sites) + 1
        
        async with httpx.AsyncClient() as client:
            for site in self.sites:
                await self._rate_limit()
                
                try:
                    params = {
                        "site": site,
                        "pagesize": min(results_per_site, 100),
                        "order": "desc",
                        "sort": "activity",
                        "fromdate": from_timestamp,
                        "filter": "!nNPvSNe7GZ",  # Include body excerpt
                    }
                    
                    if keywords:
                        # Use tags for filtering
                        params["tagged"] = ";".join(keywords[:5])  # Max 5 tags
                        endpoint = f"{self.BASE_URL}/questions"
                    else:
                        # Get hot questions
                        endpoint = f"{self.BASE_URL}/questions"
                        params["sort"] = "hot"
                    
                    response = await client.get(
                        endpoint,
                        params=params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    
                    # StackExchange returns gzipped JSON
                    data = response.json()
                    
                    questions = data.get("items", [])
                    
                    for q in questions:
                        title = q.get("title")
                        if not title:
                            continue
                        
                        # Parse creation date
                        pub_date = None
                        if q.get("creation_date"):
                            pub_date = datetime.fromtimestamp(
                                q.get("creation_date"), 
                                tz=timezone.utc
                            )
                        
                        # Get tags
                        tags = q.get("tags", [])[:5]
                        
                        yield NewsData(
                            title=title,
                            summary=q.get("body_markdown", "")[:500] if q.get("body_markdown") else None,
                            source=self.source_name,
                            source_id=str(q.get("question_id")),
                            url=q.get("link"),
                            published_date=pub_date,
                            author=q.get("owner", {}).get("display_name"),
                            category=self.category,
                            tags=["stackexchange", site] + tags,
                            raw_data={
                                "site": site,
                                "score": q.get("score", 0),
                                "view_count": q.get("view_count", 0),
                                "answer_count": q.get("answer_count", 0),
                                "is_answered": q.get("is_answered", False),
                            }
                        )
                        
                except Exception as e:
                    print(f"Error fetching StackExchange {site}: {e}")
                    continue
