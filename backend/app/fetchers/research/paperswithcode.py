"""Papers With Code API fetcher for ML research.

https://paperswithcode.com/api/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class PapersWithCodeFetcher(BaseFetcher):
    """Fetcher for Papers With Code ML research."""
    
    source_name = "paperswithcode"
    rate_limit = 2.0
    
    BASE_URL = "https://paperswithcode.com/api/v1"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch ML papers from Papers With Code."""
        await self._rate_limit()
        
        params = {
            "page_size": min(max_results, 50),
            "ordering": "-paper__date",
        }
        
        if keywords:
            params["q"] = " ".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/papers/",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        papers = data.get("results", [])
        
        for paper in papers:
            title = paper.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            if paper.get("published"):
                try:
                    pub_date = datetime.strptime(paper["published"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            # Authors
            authors = []
            for author_name in paper.get("authors", [])[:10]:
                authors.append(AuthorData(name=author_name))
            
            yield PaperData(
                title=title,
                abstract=paper.get("abstract"),
                authors=authors,
                source=self.source_name,
                source_id=paper.get("id", ""),
                url=paper.get("url_abs") or paper.get("paper_url"),
                published_date=pub_date,
                is_peer_reviewed=False,
                is_preprint=True,
                raw_data={
                    "proceeding": paper.get("proceeding"),
                    "tasks": paper.get("tasks", []),
                    "arxiv_id": paper.get("arxiv_id"),
                }
            )
