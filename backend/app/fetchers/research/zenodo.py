"""Zenodo API fetcher for open research.

https://developers.zenodo.org/
No API key required for read access.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class ZenodoFetcher(BaseFetcher):
    """Fetcher for Zenodo open research repository."""
    
    source_name = "zenodo"
    rate_limit = 2.0
    
    BASE_URL = "https://zenodo.org/api"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch records from Zenodo."""
        await self._rate_limit()
        
        params = {
            "size": min(max_results, 100),
            "sort": "-publication_date",
            "type": "publication",
        }
        
        if keywords:
            params["q"] = " OR ".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/records",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        hits = data.get("hits", {}).get("hits", [])
        
        for record in hits:
            metadata = record.get("metadata", {})
            title = metadata.get("title")
            if not title:
                continue
            
            # Authors
            authors = []
            for creator in metadata.get("creators", [])[:10]:
                name = creator.get("name")
                if name:
                    authors.append(AuthorData(
                        name=name,
                        affiliation=creator.get("affiliation"),
                    ))
            
            # Publication date
            pub_date = None
            date_str = metadata.get("publication_date")
            if date_str:
                try:
                    pub_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            yield PaperData(
                title=title,
                abstract=metadata.get("description"),
                authors=authors,
                source=self.source_name,
                source_id=str(record.get("id", "")),
                journal=metadata.get("journal", {}).get("title") if metadata.get("journal") else None,
                doi=record.get("doi"),
                url=record.get("links", {}).get("html"),
                published_date=pub_date,
                is_peer_reviewed=metadata.get("access_right") == "open",
                is_preprint=False,
                raw_data={
                    "resource_type": metadata.get("resource_type"),
                    "license": metadata.get("license", {}).get("id") if metadata.get("license") else None,
                }
            )
