"""Unpaywall API fetcher for open access papers.

https://unpaywall.org/products/api
Requires email in request. Rate limit: 100K/day.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class UnpaywallFetcher(BaseFetcher):
    """Fetcher for Unpaywall - finds open access versions of papers by DOI."""
    
    source_name = "unpaywall"
    rate_limit = 10.0  # 100K/day is generous
    
    BASE_URL = "https://api.unpaywall.org/v2"
    EMAIL = "contact@ppt-newsfeed.com"  # Required for API
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch open access papers from Unpaywall.
        
        Note: Unpaywall is DOI-based, so we need DOIs to query.
        This fetcher works best when combined with Crossref to get DOIs first.
        For standalone use, we'll use the feed endpoint for recent OA papers.
        """
        await self._rate_limit()
        
        # Unpaywall doesn't have a search API, but has a feed
        # For now, we'll demonstrate with sample DOIs or integration
        # In practice, this would be used to enrich papers from other sources
        
        # Use Crossref to find recent papers, then check Unpaywall for OA versions
        from app.fetchers.research.crossref import CrossrefFetcher
        
        crossref = CrossrefFetcher()
        
        async for paper in crossref.fetch(keywords=keywords, max_results=max_results, days_back=days_back):
            if paper.doi:
                await self._rate_limit()
                
                try:
                    oa_info = await self._check_oa(paper.doi)
                    if oa_info and oa_info.get("is_oa"):
                        # Enrich paper with OA info
                        best_loc = oa_info.get("best_oa_location", {})
                        paper.url = best_loc.get("url_for_pdf") or best_loc.get("url") or paper.url
                        paper.raw_data = paper.raw_data or {}
                        paper.raw_data["oa_status"] = oa_info.get("oa_status")
                        paper.raw_data["is_oa"] = True
                        paper.source = self.source_name
                        yield paper
                except Exception as e:
                    # If Unpaywall fails, just skip enrichment
                    continue
    
    async def _check_oa(self, doi: str) -> Optional[dict]:
        """Check if a DOI has an open access version."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{doi}",
                params={"email": self.EMAIL},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def enrich_paper(self, paper: PaperData) -> PaperData:
        """Enrich a paper with Unpaywall OA information."""
        if not paper.doi:
            return paper
        
        await self._rate_limit()
        
        try:
            oa_info = await self._check_oa(paper.doi)
            if oa_info and oa_info.get("is_oa"):
                best_loc = oa_info.get("best_oa_location", {})
                paper.url = best_loc.get("url_for_pdf") or best_loc.get("url") or paper.url
                paper.raw_data = paper.raw_data or {}
                paper.raw_data["oa_status"] = oa_info.get("oa_status")
                paper.raw_data["is_oa"] = True
        except Exception:
            pass
        
        return paper
