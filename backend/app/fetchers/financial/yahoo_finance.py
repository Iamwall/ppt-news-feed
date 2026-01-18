"""Yahoo Finance news fetcher using yfinance library.

https://github.com/ranaroussi/yfinance
No API key required. Rate limit: Be reasonable (~5 req/sec).
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import asyncio

from app.fetchers.base import BaseNewsFetcher, NewsData


class YahooFinanceFetcher(BaseNewsFetcher):
    """Fetcher for Yahoo Finance news using yfinance."""
    
    source_name = "yahoo_finance"
    category = "financial"
    rate_limit = 2.0
    requires_api_key = False
    
    def __init__(self, tickers: Optional[List[str]] = None):
        super().__init__()
        # Default to major indices and popular stocks
        self.tickers = tickers or ["^GSPC", "^DJI", "^IXIC", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch news from Yahoo Finance.
        
        Keywords are interpreted as ticker symbols.
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError("yfinance not installed. Run: pip install yfinance")
        
        # Use keywords as tickers if provided
        tickers_to_fetch = keywords if keywords else self.tickers
        
        results_per_ticker = max_results // len(tickers_to_fetch) + 1
        
        for ticker_symbol in tickers_to_fetch:
            await self._rate_limit()
            
            try:
                # Run yfinance in thread pool (it's sync)
                ticker = yf.Ticker(ticker_symbol)
                
                # Get news - yfinance returns a list of news items
                news_items = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: ticker.news
                )
                
                if not news_items:
                    continue
                
                for item in news_items[:results_per_ticker]:
                    title = item.get("title")
                    if not title:
                        continue
                    
                    # Parse timestamp
                    pub_date = None
                    timestamp = item.get("providerPublishTime")
                    if timestamp:
                        pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    
                    yield NewsData(
                        title=title,
                        summary=None,  # yfinance doesn't provide summaries
                        source=self.source_name,
                        source_id=item.get("uuid", ""),
                        url=item.get("link"),
                        published_date=pub_date,
                        author=item.get("publisher"),
                        category=self.category,
                        image_url=item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url") if item.get("thumbnail") else None,
                        tags=["finance", ticker_symbol.upper(), item.get("type", "news")],
                        raw_data={
                            "ticker": ticker_symbol,
                            "publisher": item.get("publisher"),
                            "type": item.get("type"),
                            "related_tickers": item.get("relatedTickers", []),
                        }
                    )
                    
            except Exception as e:
                print(f"Error fetching Yahoo Finance news for {ticker_symbol}: {e}")
                continue
