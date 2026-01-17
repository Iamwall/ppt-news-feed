"""Semantic Scholar API fetcher."""
from datetime import datetime, timedelta
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData
from app.core.config import settings


class SemanticScholarFetcher(BaseFetcher):
    """Fetcher for Semantic Scholar with citation data."""
    
    source_name = "semantic_scholar"
    rate_limit = settings.semantic_scholar_requests_per_second
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # Fields to request
    PAPER_FIELDS = [
        "paperId", "title", "abstract", "year", "publicationDate",
        "journal", "externalIds", "url", "citationCount",
        "influentialCitationCount", "authors", "authors.name",
        "authors.affiliations", "authors.hIndex", "authors.authorId",
    ]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from Semantic Scholar."""
        
        if not keywords:
            # Semantic Scholar requires a query, use broad terms
            keywords = ["research", "study"]
        
        query = " ".join(keywords)
        
        # Calculate year filter
        from_year = datetime.now().year - 1
        
        papers = await self._search(query, max_results, from_year)
        
        # Filter by date
        from_date = datetime.now() - timedelta(days=days_back)
        
        for paper in papers:
            if paper.published_date and paper.published_date >= from_date:
                yield paper
            elif paper.published_date is None:
                # Include papers without dates
                yield paper
    
    async def _search(
        self, 
        query: str, 
        max_results: int,
        from_year: int,
    ) -> List[PaperData]:
        """Search Semantic Scholar."""
        await self._rate_limit()
        
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key
        
        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": ",".join(self.PAPER_FIELDS),
            "year": f"{from_year}-",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        papers = []
        for item in data.get("data", []):
            try:
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Error parsing Semantic Scholar item: {e}")
                continue
        
        return papers
    
    def _parse_item(self, item: dict) -> Optional[PaperData]:
        """Parse a Semantic Scholar paper."""
        
        paper_id = item.get("paperId")
        if not paper_id:
            return None
        
        # Title
        title = item.get("title", "Untitled")
        
        # Abstract
        abstract = item.get("abstract")
        
        # Authors with h-index
        authors = []
        for author in item.get("authors", []):
            name = author.get("name")
            if name:
                affiliations = author.get("affiliations", [])
                affiliation = affiliations[0] if affiliations else None
                authors.append(AuthorData(
                    name=name,
                    affiliation=affiliation,
                    h_index=author.get("hIndex"),
                    semantic_scholar_id=author.get("authorId"),
                ))
        
        # Journal
        journal_info = item.get("journal", {})
        journal = journal_info.get("name") if journal_info else None
        
        # External IDs
        external_ids = item.get("externalIds", {})
        doi = external_ids.get("DOI")
        arxiv_id = external_ids.get("ArXiv")
        pubmed_id = external_ids.get("PubMed")
        
        # Published date
        pub_date = None
        date_str = item.get("publicationDate")
        if date_str:
            try:
                pub_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # Try just year
                year = item.get("year")
                if year:
                    pub_date = datetime(year, 1, 1)
        
        # Citation metrics
        citations = item.get("citationCount")
        influential = item.get("influentialCitationCount")
        
        # URL
        url = item.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"
        
        # Determine if preprint
        is_preprint = bool(arxiv_id) and not doi
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=paper_id,
            journal=journal,
            doi=doi,
            url=url,
            published_date=pub_date,
            citations=citations,
            influential_citations=influential,
            is_peer_reviewed=not is_preprint,
            is_preprint=is_preprint,
            raw_data={
                "arxiv_id": arxiv_id,
                "pubmed_id": pubmed_id,
            },
        )
    
    async def enrich_paper(self, paper: PaperData) -> PaperData:
        """Enrich a paper with Semantic Scholar citation data."""
        if not paper.doi:
            return paper
        
        await self._rate_limit()
        
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/DOI:{paper.doi}",
                    params={"fields": "citationCount,influentialCitationCount,authors.hIndex"},
                    headers=headers,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    paper.citations = data.get("citationCount")
                    paper.influential_citations = data.get("influentialCitationCount")
                    
                    # Update author h-indices
                    for i, author_data in enumerate(data.get("authors", [])):
                        if i < len(paper.authors):
                            paper.authors[i].h_index = author_data.get("hIndex")
        except Exception as e:
            print(f"Error enriching paper from Semantic Scholar: {e}")
        
        return paper
