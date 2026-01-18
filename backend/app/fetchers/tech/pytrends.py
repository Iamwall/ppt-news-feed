"""PyTrends fetcher for Google Trends data.

Uses unofficial Google Trends API via pytrends library.
No API key required but may be rate limited.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import asyncio

from app.fetchers.base import BaseNewsFetcher, NewsData


class PyTrendsFetcher(BaseNewsFetcher):
    """Fetcher for Google Trends via PyTrends."""
    
    source_name = "pytrends"
    category = "tech"
    rate_limit = 0.2  # Very conservative - Google rate limits
    requires_api_key = False
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch trending searches and interest data from Google Trends.
        
        Keywords are used to find related trending topics.
        """
        try:
            from pytrends.request import TrendReq
        except ImportError:
            raise ImportError("pytrends not installed. Run: pip install pytrends")
        
        await self._rate_limit()
        
        # Run pytrends in thread pool (it's sync)
        loop = asyncio.get_event_loop()
        
        try:
            # Initialize pytrends
            pytrends = await loop.run_in_executor(
                None,
                lambda: TrendReq(hl='en-US', tz=360)
            )
            
            if keywords:
                # Get related queries for keywords
                await loop.run_in_executor(
                    None,
                    lambda: pytrends.build_payload(keywords[:5], timeframe=f'now {days_back}-d')
                )
                
                related = await loop.run_in_executor(
                    None,
                    pytrends.related_queries
                )
                
                count = 0
                for kw, data in related.items():
                    if count >= max_results:
                        break
                    
                    # Rising queries
                    rising = data.get("rising")
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(5).iterrows():
                            if count >= max_results:
                                break
                            
                            query = row.get("query", "")
                            if query:
                                yield NewsData(
                                    title=f"Rising: {query}",
                                    summary=f"Related to '{kw}' - Rising interest",
                                    source=self.source_name,
                                    source_id=f"rising_{kw}_{query}",
                                    url=f"https://trends.google.com/trends/explore?q={query.replace(' ', '%20')}",
                                    published_date=datetime.now(timezone.utc),
                                    author="Google Trends",
                                    category=self.category,
                                    tags=["trends", "rising", kw],
                                    raw_data={
                                        "related_to": kw,
                                        "value": row.get("value"),
                                    }
                                )
                                count += 1
            else:
                # Get trending searches for today
                trending = await loop.run_in_executor(
                    None,
                    lambda: pytrends.trending_searches(pn='united_states')
                )
                
                count = 0
                for idx, row in trending.head(max_results).iterrows():
                    query = row[0] if len(row) > 0 else None
                    if query:
                        yield NewsData(
                            title=f"Trending: {query}",
                            summary="Trending on Google",
                            source=self.source_name,
                            source_id=f"trending_{query}",
                            url=f"https://trends.google.com/trends/explore?q={query.replace(' ', '%20')}",
                            published_date=datetime.now(timezone.utc),
                            author="Google Trends",
                            category=self.category,
                            tags=["trends", "google"],
                            raw_data={}
                        )
                        count += 1
                        
        except Exception as e:
            print(f"PyTrends error: {e}")
            return
