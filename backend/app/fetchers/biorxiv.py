from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class BioRxivFetcher(BaseFetcher):
    """Fetcher for bioRxiv and medRxiv preprints."""
    
    source_name = "biorxiv"
    rate_limit = 5.0  # Generous rate limit
    
    # API endpoints
    BIORXIV_API = "https://api.biorxiv.org/details/biorxiv"
    MEDRXIV_API = "https://api.biorxiv.org/details/medrxiv"
    
    def __init__(self, server: str = "biorxiv"):
        super().__init__()
        self.server = server
        self.source_name = server
        self.base_url = self.MEDRXIV_API if server == "medrxiv" else self.BIORXIV_API
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from bioRxiv/medRxiv."""
        
        # Calculate date range
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Fetch papers in batches (API returns max 100 per request)
        cursor = 0
        batch_size = min(100, max_results)
        fetched = 0
        
        while fetched < max_results:
            papers = await self._fetch_batch(from_date, to_date, cursor)
            
            if not papers:
                break
            
            for paper in papers:
                # Filter by keywords if provided
                if keywords:
                    text = f"{paper.title} {paper.abstract or ''}".lower()
                    if not any(kw.lower() in text for kw in keywords):
                        continue
                
                yield paper
                fetched += 1
                
                if fetched >= max_results:
                    break
            
            cursor += len(papers)
            
            # Safety check
            if len(papers) < batch_size:
                break
    
    async def _fetch_batch(
        self, 
        from_date: str, 
        to_date: str, 
        cursor: int,
    ) -> List[PaperData]:
        """Fetch a batch of papers."""
        await self._rate_limit()
        
        url = f"{self.base_url}/{from_date}/{to_date}/{cursor}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()
            data = response.json()
        
        collection = data.get("collection", [])
        papers = []
        
        for item in collection:
            try:
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Error parsing {self.source_name} item: {e}")
                continue
        
        return papers
    
    def _parse_item(self, item: dict) -> Optional[PaperData]:
        """Parse a single bioRxiv/medRxiv item."""
        
        doi = item.get("doi")
        if not doi:
            return None
        
        # Title
        title = item.get("title", "Untitled")
        
        # Abstract
        abstract = item.get("abstract")
        
        # Authors (comes as semicolon-separated string)
        authors = []
        author_str = item.get("authors", "")
        if author_str:
            for name in author_str.split(";"):
                name = name.strip()
                if name:
                    authors.append(AuthorData(name=name))
        
        # Published date
        pub_date = None
        date_str = item.get("date")
        if date_str:
            try:
                pub_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Category
        category = item.get("category", "")
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=doi,
            journal=f"{self.source_name.capitalize()} Preprint",
            doi=doi,
            url=f"https://doi.org/{doi}",
            published_date=pub_date,
            is_peer_reviewed=False,
            is_preprint=True,
            raw_data={"category": category, "version": item.get("version")},
        )
