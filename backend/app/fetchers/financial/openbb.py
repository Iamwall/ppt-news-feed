"""OpenBB SDK integration for financial data.

https://openbb.co/
Uses OpenBB Terminal SDK for data.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import asyncio

from app.fetchers.base import BaseNewsFetcher, NewsData


class OpenBBFetcher(BaseNewsFetcher):
    """Fetcher using OpenBB SDK for market data."""
    
    source_name = "openbb"
    category = "financial"
    rate_limit = 1.0
    requires_api_key = False  # Uses free data sources
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch financial data from OpenBB SDK."""
        try:
            from openbb import obb
        except ImportError:
            print("OpenBB SDK not installed. Run: pip install openbb")
            return
        
        await self._rate_limit()
        
        symbols = keywords if keywords else ["AAPL", "MSFT"]
        
        loop = asyncio.get_event_loop()
        
        for symbol in symbols[:5]:
            try:
                # Get company news using OpenBB
                news = await loop.run_in_executor(
                    None,
                    lambda: obb.news.company(symbol=symbol, limit=max_results // len(symbols))
                )
                
                for item in news.results:
                    yield NewsData(
                        title=item.title,
                        summary=item.text[:500] if hasattr(item, 'text') else None,
                        source=self.source_name,
                        source_id=str(hash(item.title)),
                        url=item.url if hasattr(item, 'url') else None,
                        published_date=item.date if hasattr(item, 'date') else datetime.now(timezone.utc),
                        author=item.source if hasattr(item, 'source') else None,
                        category=self.category,
                        tags=["openbb", "finance", symbol],
                        raw_data={}
                    )
            except Exception as e:
                print(f"OpenBB error for {symbol}: {e}")
                continue
