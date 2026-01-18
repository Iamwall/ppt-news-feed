"""OpenAlex API fetcher for scientific papers.

https://openalex.org/
No API key required. Rate limit: 10 requests/second, 100K/day.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class OpenAlexFetcher(BaseFetcher):
    """Fetcher for OpenAlex - open catalog of global scholarly papers."""
    
    source_name = "openalex"
    rate_limit = 5.0  # Conservative
    
    BASE_URL = "https://api.openalex.org"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from OpenAlex."""
        await self._rate_limit()
        
        # Calculate date range
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        from_date_str = from_date.strftime("%Y-%m-%d")
        
        # Build query parameters
        params = {
            "per_page": min(max_results, 200),  # API max is 200
            "sort": "publication_date:desc",
            "filter": f"from_publication_date:{from_date_str}",
        }
        
        if keywords:
            # Search in title and abstract
            search_query = " ".join(keywords)
            params["search"] = search_query
        
        # Add polite pool email for better rate limits
        params["mailto"] = "contact@example.com"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        
        for work in results:
            try:
                paper = self._parse_work(work)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing OpenAlex work: {e}")
                continue
    
    def _parse_work(self, work: dict) -> Optional[PaperData]:
        """Parse a single OpenAlex work into PaperData."""
        title = work.get("title")
        if not title:
            return None
        
        # Get OpenAlex ID
        openalex_id = work.get("id", "").replace("https://openalex.org/", "")
        
        # Parse authors
        authors = []
        for authorship in work.get("authorships", [])[:10]:  # Limit authors
            author_info = authorship.get("author", {})
            name = author_info.get("display_name")
            if name:
                # Get first institution
                institutions = authorship.get("institutions", [])
                affiliation = institutions[0].get("display_name") if institutions else None
                authors.append(AuthorData(
                    name=name,
                    affiliation=affiliation,
                ))
        
        # Parse publication date
        pub_date = None
        pub_date_str = work.get("publication_date")
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        # Get abstract if available
        abstract_inverted = work.get("abstract_inverted_index")
        abstract = None
        if abstract_inverted:
            # OpenAlex stores abstract as inverted index, reconstruct
            try:
                word_positions = [(word, min(positions)) for word, positions in abstract_inverted.items()]
                word_positions.sort(key=lambda x: x[1])
                abstract = " ".join(word for word, _ in word_positions)
            except Exception:
                pass
        
        # Get primary location for journal/source
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        journal = source.get("display_name")
        
        # DOI
        doi = work.get("doi")
        if doi:
            doi = doi.replace("https://doi.org/", "")
        
        # URL
        url = work.get("doi") or primary_location.get("landing_page_url")
        
        # Is it open access?
        is_oa = work.get("open_access", {}).get("is_oa", False)
        
        # Check if it's a preprint
        work_type = work.get("type", "")
        is_preprint = "preprint" in work_type.lower()
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=openalex_id,
            journal=journal,
            doi=doi,
            url=url,
            published_date=pub_date,
            citations=work.get("cited_by_count"),
            is_peer_reviewed=not is_preprint,
            is_preprint=is_preprint,
            raw_data={
                "type": work_type,
                "is_oa": is_oa,
                "concepts": [c.get("display_name") for c in work.get("concepts", [])[:5]],
            }
        )
