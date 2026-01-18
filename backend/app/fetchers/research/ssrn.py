"""SSRN API fetcher for social sciences research.

https://www.ssrn.com/
No official API - uses search endpoint.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class SSRNFetcher(BaseFetcher):
    """Fetcher for SSRN social sciences preprints."""
    
    source_name = "ssrn"
    rate_limit = 1.0
    
    BASE_URL = "https://www.ssrn.com/api"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from SSRN."""
        await self._rate_limit()
        
        # SSRN has RSS feeds we can use
        import feedparser
        
        # Use the main RSS feed
        feed_url = "https://papers.ssrn.com/sol3/Jeljour_results.cfm?form_name=journalBrowse&journal_id=1551429&output=rss"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(feed_url, timeout=30.0)
            response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        count = 0
        for entry in feed.entries:
            if count >= max_results:
                break
            
            title = entry.get("title", "")
            if not title:
                continue
            
            # Filter by keywords
            if keywords:
                combined = (title + " " + entry.get("summary", "")).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            # Parse date
            pub_date = None
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            # Parse authors
            authors = []
            author = entry.get("author", "")
            if author:
                for name in author.split(",")[:5]:
                    authors.append(AuthorData(name=name.strip()))
            
            yield PaperData(
                title=title,
                abstract=entry.get("summary", "")[:2000] if entry.get("summary") else None,
                authors=authors,
                source=self.source_name,
                source_id=entry.get("id", ""),
                url=entry.get("link"),
                published_date=pub_date,
                is_peer_reviewed=False,
                is_preprint=True,
                raw_data={}
            )
            count += 1
