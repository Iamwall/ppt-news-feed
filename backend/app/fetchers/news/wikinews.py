"""WikiNews API fetcher.

https://en.wikinews.org/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class WikiNewsFetcher(BaseNewsFetcher):
    """Fetcher for WikiNews articles."""
    
    source_name = "wikinews"
    category = "news"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://en.wikinews.org/w/api.php"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch articles from WikiNews."""
        await self._rate_limit()
        
        params = {
            "action": "query",
            "format": "json",
            "list": "recentchanges",
            "rcnamespace": "0",  # Main namespace
            "rclimit": min(max_results, 50),
            "rctype": "new",
            "rcprop": "title|timestamp|user|comment",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        changes = data.get("query", {}).get("recentchanges", [])
        
        for change in changes:
            title = change.get("title", "")
            if not title:
                continue
            
            # Filter by keywords
            if keywords:
                if not any(kw.lower() in title.lower() for kw in keywords):
                    continue
            
            # Parse date
            pub_date = None
            if change.get("timestamp"):
                try:
                    pub_date = datetime.fromisoformat(change["timestamp"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            yield NewsData(
                title=title,
                summary=change.get("comment"),
                source=self.source_name,
                source_id=str(change.get("rcid", "")),
                url=f"https://en.wikinews.org/wiki/{title.replace(' ', '_')}",
                published_date=pub_date,
                author=change.get("user"),
                category=self.category,
                tags=["wikinews", "wiki"],
                raw_data={}
            )
