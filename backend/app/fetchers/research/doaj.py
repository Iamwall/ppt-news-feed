"""DOAJ (Directory of Open Access Journals) API fetcher.

https://doaj.org/api/
No API key required. Rate limit: Be reasonable.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class DOAJFetcher(BaseFetcher):
    """Fetcher for DOAJ open access journal articles."""
    
    source_name = "doaj"
    rate_limit = 2.0
    
    BASE_URL = "https://doaj.org/api/v2"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch open access articles from DOAJ."""
        await self._rate_limit()
        
        # Build search query (DOAJ v2 uses path-based search)
        if keywords:
            search_query = "+".join(keywords)
        else:
            search_query = "*"
        
        params = {
            "pageSize": min(max_results, 100),
            "sort": "last_updated:desc",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/articles/{search_query}",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        
        for item in results:
            try:
                paper = self._parse_article(item)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing DOAJ article: {e}")
                continue
    
    def _parse_article(self, item: dict) -> Optional[PaperData]:
        """Parse a single DOAJ article."""
        bibjson = item.get("bibjson", {})
        
        title = bibjson.get("title")
        if not title:
            return None
        
        # Authors
        authors = []
        for author in bibjson.get("author", [])[:10]:
            name = author.get("name")
            if name:
                authors.append(AuthorData(
                    name=name,
                    affiliation=author.get("affiliation"),
                ))
        
        # Abstract
        abstract = bibjson.get("abstract")
        
        # Publication date
        pub_date = None
        year = bibjson.get("year")
        month = bibjson.get("month", "01")
        if year:
            try:
                pub_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        # Journal info
        journal = bibjson.get("journal", {})
        journal_title = journal.get("title")
        
        # Identifiers
        identifiers = bibjson.get("identifier", [])
        doi = None
        for ident in identifiers:
            if ident.get("type") == "doi":
                doi = ident.get("id")
                break
        
        # Link
        links = bibjson.get("link", [])
        url = links[0].get("url") if links else None
        if doi and not url:
            url = f"https://doi.org/{doi}"
        
        # Keywords/subjects
        subjects = bibjson.get("subject", [])
        subject_terms = [s.get("term") for s in subjects if s.get("term")]
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=item.get("id", ""),
            journal=journal_title,
            doi=doi,
            url=url,
            published_date=pub_date,
            is_peer_reviewed=True,  # DOAJ only indexes peer-reviewed journals
            is_preprint=False,
            raw_data={
                "subjects": subject_terms,
                "publisher": journal.get("publisher"),
                "issns": journal.get("issns", []),
            }
        )
