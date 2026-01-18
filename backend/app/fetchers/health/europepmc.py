"""Europe PMC API fetcher for biomedical literature.

https://europepmc.org/RestfulWebService
No API key required. Rate limit: Be reasonable.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class EuropePMCFetcher(BaseFetcher):
    """Fetcher for Europe PMC biomedical and life sciences literature."""
    
    source_name = "europepmc"
    rate_limit = 3.0
    
    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch articles from Europe PMC."""
        await self._rate_limit()
        
        # Build query
        query_parts = []
        if keywords:
            query_parts.append(" OR ".join(f'"{kw}"' for kw in keywords))
        else:
            query_parts.append("*")
        
        # Date filter
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        query_parts.append(f"FIRST_PDATE:[{from_date.strftime('%Y-%m-%d')} TO *]")
        
        params = {
            "query": " AND ".join(query_parts),
            "format": "json",
            "pageSize": min(max_results, 100),
            "sort": "P_PDATE_D desc",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        results = data.get("resultList", {}).get("result", [])
        
        for item in results:
            try:
                paper = self._parse_article(item)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing Europe PMC article: {e}")
                continue
    
    def _parse_article(self, item: dict) -> Optional[PaperData]:
        """Parse a single Europe PMC article."""
        title = item.get("title")
        if not title:
            return None
        
        # Authors
        authors = []
        author_string = item.get("authorString", "")
        for name in author_string.split(", ")[:10]:
            if name:
                authors.append(AuthorData(name=name.strip()))
        
        # Publication date
        pub_date = None
        date_str = item.get("firstPublicationDate")
        if date_str:
            try:
                pub_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        # DOI
        doi = item.get("doi")
        
        # URL
        pmid = item.get("pmid")
        pmcid = item.get("pmcid")
        if pmcid:
            url = f"https://europepmc.org/article/PMC/{pmcid}"
        elif pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        elif doi:
            url = f"https://doi.org/{doi}"
        else:
            url = None
        
        return PaperData(
            title=title,
            abstract=item.get("abstractText"),
            authors=authors,
            source=self.source_name,
            source_id=pmid or pmcid or doi or "",
            journal=item.get("journalTitle"),
            doi=doi,
            url=url,
            published_date=pub_date,
            citations=item.get("citedByCount"),
            is_peer_reviewed=True,
            is_preprint=item.get("source") == "PPR",
            raw_data={
                "pmid": pmid,
                "pmcid": pmcid,
                "source": item.get("source"),
                "isOpenAccess": item.get("isOpenAccess") == "Y",
            }
        )
