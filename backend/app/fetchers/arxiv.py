"""arXiv API fetcher."""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx
from xml.etree import ElementTree
import re

from app.fetchers.base import BaseFetcher, PaperData, AuthorData
from app.core.config import settings


class ArxivFetcher(BaseFetcher):
    """Fetcher for arXiv using their API."""
    
    source_name = "arxiv"
    rate_limit = settings.arxiv_requests_per_second
    
    BASE_URL = "https://export.arxiv.org/api/query"
    ATOM_NS = "{http://www.w3.org/2005/Atom}"
    ARXIV_NS = "{http://arxiv.org/schemas/atom}"
    
    # arXiv categories
    CATEGORIES = [
        "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
        "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph",
        "math", "cs", "q-bio", "q-fin", "stat", "eess", "econ",
    ]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from arXiv."""
        
        # Build search query
        query_parts = []
        
        if keywords:
            # Search in title and abstract
            keyword_query = " OR ".join(f'all:"{k}"' for k in keywords)
            query_parts.append(f"({keyword_query})")
        else:
            # Get recent from all categories
            query_parts.append("cat:*")
        
        query = " AND ".join(query_parts) if query_parts else "cat:*"
        
        # Calculate date range for filtering
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Fetch papers
        papers = await self._search(query, max_results)
        
        for paper in papers:
            # Filter by date if available
            if paper.published_date and paper.published_date >= from_date:
                yield paper
            elif paper.published_date is None:
                yield paper
    
    async def _search(self, query: str, max_results: int) -> List[PaperData]:
        """Search arXiv and return papers."""
        await self._rate_limit()
        
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
        
        # Parse Atom feed
        root = ElementTree.fromstring(response.content)
        papers = []
        
        for entry in root.findall(f"{self.ATOM_NS}entry"):
            try:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Error parsing arXiv entry: {e}")
                continue
        
        return papers
    
    def _parse_entry(self, entry: ElementTree.Element) -> Optional[PaperData]:
        """Parse a single arXiv entry."""
        
        # ID
        id_elem = entry.find(f"{self.ATOM_NS}id")
        if id_elem is None:
            return None
        
        arxiv_id = id_elem.text
        # Extract just the ID part (e.g., "2401.12345v1")
        match = re.search(r'abs/(.+)$', arxiv_id)
        source_id = match.group(1) if match else arxiv_id
        
        # Title
        title_elem = entry.find(f"{self.ATOM_NS}title")
        title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "Untitled"
        
        # Abstract (summary)
        summary_elem = entry.find(f"{self.ATOM_NS}summary")
        abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else None
        
        # Authors
        authors = []
        for author_elem in entry.findall(f"{self.ATOM_NS}author"):
            name_elem = author_elem.find(f"{self.ATOM_NS}name")
            if name_elem is not None:
                affil_elem = author_elem.find(f"{self.ARXIV_NS}affiliation")
                affiliation = affil_elem.text if affil_elem is not None else None
                authors.append(AuthorData(name=name_elem.text, affiliation=affiliation))
        
        # Published date
        published_elem = entry.find(f"{self.ATOM_NS}published")
        pub_date = None
        if published_elem is not None:
            try:
                pub_date = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        # DOI (if available)
        doi = None
        doi_elem = entry.find(f"{self.ARXIV_NS}doi")
        if doi_elem is not None:
            doi = doi_elem.text
        
        # PDF link
        pdf_link = None
        for link in entry.findall(f"{self.ATOM_NS}link"):
            if link.get("title") == "pdf":
                pdf_link = link.get("href")
                break
        
        # Categories
        categories = []
        for cat in entry.findall(f"{self.ARXIV_NS}primary_category"):
            categories.append(cat.get("term"))
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=source_id,
            journal=f"arXiv:{source_id.split('v')[0]}",  # Remove version
            doi=doi,
            url=f"https://arxiv.org/abs/{source_id}",
            published_date=pub_date,
            is_peer_reviewed=False,
            is_preprint=True,
            raw_data={"categories": categories, "pdf_link": pdf_link},
        )
