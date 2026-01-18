"""GDELT Project API fetcher for global news.

https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
No API key required. The largest open database of human society.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx
import csv
from io import StringIO

from app.fetchers.base import BaseNewsFetcher, NewsData


class GDELTFetcher(BaseNewsFetcher):
    """Fetcher for GDELT Project global news database."""
    
    source_name = "gdelt"
    category = "news"
    rate_limit = 1.0  # Be polite
    requires_api_key = False
    
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch global news from GDELT.
        
        GDELT monitors news from around the world in 65+ languages.
        """
        await self._rate_limit()
        
        # Build query
        query_parts = []
        if keywords:
            query_parts.append(" OR ".join(keywords))
        else:
            query_parts.append("*")  # All news
        
        # GDELT uses specific timespan format
        timespan = f"{days_back}d"  # e.g., "7d" for 7 days
        
        params = {
            "query": " ".join(query_parts),
            "mode": "artlist",  # Article list mode
            "maxrecords": min(max_results, 250),
            "format": "json",
            "timespan": timespan,
            "sort": "datedesc",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        articles = data.get("articles", [])
        
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            date_str = article.get("seendate")
            if date_str:
                try:
                    pub_date = datetime.strptime(date_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            yield NewsData(
                title=title,
                summary=None,  # GDELT API doesn't provide summaries
                source=self.source_name,
                source_id=article.get("url", ""),  # Use URL as ID
                url=article.get("url"),
                published_date=pub_date,
                author=article.get("domain"),
                category=self.category,
                image_url=article.get("socialimage"),
                tags=["gdelt", "global"],
                raw_data={
                    "domain": article.get("domain"),
                    "language": article.get("language"),
                    "sourcecountry": article.get("sourcecountry"),
                }
            )
