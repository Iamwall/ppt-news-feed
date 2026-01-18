"""SciHub mirror fetcher.

For accessing research papers. Uses RSS.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class SciOpenFetcher(BaseFetcher):
    """Fetcher for open science papers via Sci-Hub RSS mirrors."""
    
    source_name = "sciopen"
    rate_limit = 1.0
    
    # Science Open and other open paper aggregators
    FEEDS = [
        "https://www.scienceopen.com/feed/latest",
    ]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from open science sources."""
        await self._rate_limit()
        
        async with httpx.AsyncClient() as client:
            for feed_url in self.FEEDS:
                try:
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
                        
                        if keywords:
                            combined = (title + " " + entry.get("summary", "")).lower()
                            if not any(kw.lower() in combined for kw in keywords):
                                continue
                        
                        pub_date = None
                        if entry.get("published_parsed"):
                            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        
                        authors = []
                        for author in entry.get("authors", [])[:10]:
                            if author.get("name"):
                                authors.append(AuthorData(name=author["name"]))
                        
                        yield PaperData(
                            title=title,
                            abstract=entry.get("summary", "")[:2000] if entry.get("summary") else None,
                            authors=authors,
                            source=self.source_name,
                            source_id=entry.get("id", ""),
                            url=entry.get("link"),
                            published_date=pub_date,
                            is_peer_reviewed=True,
                            is_preprint=False,
                            raw_data={}
                        )
                        count += 1
                except Exception:
                    continue
