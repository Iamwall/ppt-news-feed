"""OSF Preprints API fetcher.

https://osf.io/preprints/
No API key required.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class OSFFetcher(BaseFetcher):
    """Fetcher for OSF Preprints."""
    
    source_name = "osf"
    rate_limit = 2.0
    
    BASE_URL = "https://api.osf.io/v2"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch preprints from OSF."""
        await self._rate_limit()
        
        params = {
            "page[size]": min(max_results, 100),
            "sort": "-date_created",
        }
        
        if keywords:
            params["filter[title,description]"] = ",".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/preprints/",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        for preprint in data.get("data", []):
            attrs = preprint.get("attributes", {})
            title = attrs.get("title")
            if not title:
                continue
            
            # Parse date
            pub_date = None
            if attrs.get("date_created"):
                try:
                    pub_date = datetime.fromisoformat(attrs["date_created"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            yield PaperData(
                title=title,
                abstract=attrs.get("description"),
                authors=[],  # Would need another request
                source=self.source_name,
                source_id=preprint.get("id", ""),
                doi=attrs.get("doi"),
                url=attrs.get("preprint_doi_url") or f"https://osf.io/{preprint.get('id', '')}",
                published_date=pub_date,
                is_peer_reviewed=False,
                is_preprint=True,
                raw_data={"provider": attrs.get("reviews_state")}
            )
