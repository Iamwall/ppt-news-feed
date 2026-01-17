"""PLOS (Public Library of Science) API fetcher."""
from datetime import datetime, timedelta
from typing import Optional, List, AsyncIterator
import httpx
from xml.etree import ElementTree

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class PLOSFetcher(BaseFetcher):
    """Fetcher for PLOS using their search API."""

    source_name = "plos"
    rate_limit = 2.0

    BASE_URL = "https://api.plos.org/search"

    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from PLOS."""

        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
        to_date = datetime.now().strftime("%Y-%m-%dT23:59:59Z")

        # Build query
        query_parts = []
        if keywords:
            keyword_query = " OR ".join(f'"{k}"' for k in keywords)
            query_parts.append(f"({keyword_query})")

        # Add date filter
        query_parts.append(f"publication_date:[{from_date} TO {to_date}]")

        query = " AND ".join(query_parts)

        # Fetch papers
        papers = await self._search(query, max_results)

        for paper in papers:
            yield paper

    async def _search(self, query: str, max_results: int) -> List[PaperData]:
        """Search PLOS API."""
        await self._rate_limit()

        params = {
            "q": query,
            "rows": min(max_results, 100),
            "start": 0,
            "wt": "json",
            "fl": "id,title,abstract,author,publication_date,journal,article_type,counter_total_all",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        papers = []
        docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            try:
                paper = self._parse_doc(doc)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Error parsing PLOS document: {e}")
                continue

        return papers

    def _parse_doc(self, doc: dict) -> Optional[PaperData]:
        """Parse a PLOS search result."""

        # DOI (PLOS uses DOI as ID)
        doi = doc.get("id")
        if not doi:
            return None

        # Title
        title = doc.get("title", ["Untitled"])[0] if isinstance(doc.get("title"), list) else doc.get("title", "Untitled")

        # Abstract
        abstract_list = doc.get("abstract", [])
        abstract = abstract_list[0] if abstract_list else None

        # Authors
        authors = []
        author_list = doc.get("author", [])
        if isinstance(author_list, list):
            for author_name in author_list[:10]:  # Limit to first 10 authors
                authors.append(AuthorData(name=author_name))

        # Journal
        journal = doc.get("journal", "PLOS")

        # Published date
        pub_date = None
        date_str = doc.get("publication_date")
        if date_str:
            try:
                pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Article type (for preprint detection)
        article_type = doc.get("article_type", "")
        is_preprint = "preprint" in article_type.lower() if article_type else False

        # Views/downloads as proxy for impact
        views = doc.get("counter_total_all", 0)

        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=doi,
            journal=journal,
            doi=doi,
            url=f"https://doi.org/{doi}",
            published_date=pub_date,
            is_peer_reviewed=not is_preprint,
            is_preprint=is_preprint,
            raw_data={"views": views, "article_type": article_type},
        )
