"""SEC EDGAR API fetcher for company filings.

https://www.sec.gov/developer
No API key required. Requires User-Agent header.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class SECEdgarFetcher(BaseNewsFetcher):
    """Fetcher for SEC EDGAR company filings."""
    
    source_name = "sec_edgar"
    category = "financial"
    rate_limit = 0.1  # SEC requires 10 requests/second max
    requires_api_key = False
    
    BASE_URL = "https://data.sec.gov"
    
    HEADERS = {
        "User-Agent": "PPT-NewsFeed/1.0 (contact@ppt-newsfeed.com)",
        "Accept-Encoding": "gzip, deflate",
    }
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch recent SEC filings."""
        await self._rate_limit()
        
        async with httpx.AsyncClient(headers=self.HEADERS) as client:
            # Get recent filings
            response = await client.get(
                f"{self.BASE_URL}/submissions/submissions.json",
                timeout=30.0,
            )
            
            if response.status_code == 403:
                print("SEC EDGAR: Access denied. Check User-Agent.")
                return
            
            response.raise_for_status()
            
            # Get latest filings RSS
            response = await client.get(
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-K&company=&dateb=&owner=include&count=40&output=atom",
                timeout=30.0,
            )
            response.raise_for_status()
            
            # Parse Atom feed
            import feedparser
            feed = feedparser.parse(response.text)
            
            count = 0
            for entry in feed.entries:
                if count >= max_results:
                    break
                
                title = entry.get("title", "")
                if not title:
                    continue
                
                # Filter by keywords (company names)
                if keywords:
                    if not any(kw.lower() in title.lower() for kw in keywords):
                        continue
                
                # Parse date
                pub_date = None
                if entry.get("updated_parsed"):
                    pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                yield NewsData(
                    title=f"SEC Filing: {title}",
                    summary=entry.get("summary", "")[:500] if entry.get("summary") else None,
                    source=self.source_name,
                    source_id=entry.get("id", ""),
                    url=entry.get("link"),
                    published_date=pub_date,
                    author="SEC",
                    category=self.category,
                    tags=["sec", "edgar", "filings"],
                    raw_data={
                        "category": entry.get("category", {}).get("term") if entry.get("category") else None,
                    }
                )
                count += 1
