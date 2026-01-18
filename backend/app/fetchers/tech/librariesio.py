"""Libraries.io API fetcher for open source package trends.

https://libraries.io/api
Requires API key. Free tier: 60 req/min.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class LibrariesIOFetcher(BaseNewsFetcher):
    """Fetcher for Libraries.io open source package trends."""
    
    source_name = "librariesio"
    category = "tech"
    rate_limit = 1.0
    requires_api_key = True
    
    BASE_URL = "https://libraries.io/api"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("LIBRARIESIO_KEY")
        if not self.api_key:
            raise ValueError("LIBRARIESIO_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch trending packages from Libraries.io.
        
        Keywords filter by platform (npm, pypi, etc.) or package name.
        """
        await self._rate_limit()
        
        # Default platforms
        platforms = ["npm", "pypi", "rubygems", "maven"]
        
        # If keywords look like platforms, use them
        if keywords:
            platform_keywords = [k.lower() for k in keywords if k.lower() in platforms]
            if platform_keywords:
                platforms = platform_keywords
        
        results_per_platform = max_results // len(platforms) + 1
        
        async with httpx.AsyncClient() as client:
            for platform in platforms:
                await self._rate_limit()
                
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/search",
                        params={
                            "api_key": self.api_key,
                            "platforms": platform,
                            "sort": "rank",
                            "per_page": min(results_per_platform, 30),
                        },
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    packages = response.json()
                    
                    for pkg in packages:
                        name = pkg.get("name")
                        if not name:
                            continue
                        
                        # Filter by name keywords
                        if keywords and not any(k.lower() in k for k in keywords if k.lower() not in platforms):
                            pass  # Don't filter if all keywords are platforms
                        
                        # Parse date
                        pub_date = None
                        date_str = pkg.get("latest_release_published_at")
                        if date_str:
                            try:
                                pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            except ValueError:
                                pass
                        
                        yield NewsData(
                            title=f"{name} ({platform}): {pkg.get('latest_release_number', 'latest')}",
                            summary=pkg.get("description"),
                            source=self.source_name,
                            source_id=f"{platform}_{name}",
                            url=pkg.get("repository_url") or pkg.get("homepage"),
                            published_date=pub_date,
                            author=None,
                            category=self.category,
                            tags=["opensource", platform, pkg.get("language", "").lower()],
                            raw_data={
                                "platform": platform,
                                "stars": pkg.get("stars"),
                                "rank": pkg.get("rank"),
                                "dependents_count": pkg.get("dependents_count"),
                                "language": pkg.get("language"),
                            }
                        )
                        
                except Exception as e:
                    print(f"Error fetching Libraries.io {platform}: {e}")
                    continue
