"""CoinGecko API fetcher for cryptocurrency trends.

https://www.coingecko.com/en/api
No API key required for basic endpoints. Rate limit: 10-30 calls/min.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class CoinGeckoFetcher(BaseNewsFetcher):
    """Fetcher for CoinGecko cryptocurrency trends and news."""
    
    source_name = "coingecko"
    category = "financial"
    rate_limit = 0.5  # Conservative: 30 calls/min = 0.5/sec
    requires_api_key = False
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch trending coins and market data from CoinGecko.
        
        Keywords can be coin IDs like 'bitcoin', 'ethereum', etc.
        If no keywords, fetches trending coins.
        """
        await self._rate_limit()
        
        async with httpx.AsyncClient() as client:
            # Get trending coins (most searched in last 24h)
            response = await client.get(
                f"{self.BASE_URL}/search/trending",
                timeout=30.0
            )
            response.raise_for_status()
            trending_data = response.json()
        
        coins = trending_data.get("coins", [])
        
        for coin_data in coins[:max_results]:
            item = coin_data.get("item", {})
            
            coin_id = item.get("id", "")
            name = item.get("name", "")
            symbol = item.get("symbol", "").upper()
            
            # Filter by keywords if provided
            if keywords:
                combined = f"{coin_id} {name} {symbol}".lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            # Get additional coin data
            await self._rate_limit()
            
            try:
                async with httpx.AsyncClient() as client:
                    coin_response = await client.get(
                        f"{self.BASE_URL}/coins/{coin_id}",
                        params={
                            "localization": "false",
                            "tickers": "false",
                            "community_data": "false",
                            "developer_data": "false",
                        },
                        timeout=30.0
                    )
                    coin_response.raise_for_status()
                    coin_info = coin_response.json()
            except Exception:
                coin_info = {}
            
            # Build summary from description or market data
            description = coin_info.get("description", {}).get("en", "")
            if description:
                # Truncate description
                summary = description[:500] + "..." if len(description) > 500 else description
                # Remove HTML tags
                import re
                summary = re.sub(r'<[^>]+>', '', summary)
            else:
                market_cap_rank = item.get("market_cap_rank", "N/A")
                summary = f"{name} ({symbol}) - Market Cap Rank: #{market_cap_rank}"
            
            # Price change info
            price_btc = item.get("price_btc", 0)
            
            yield NewsData(
                title=f"Trending: {name} ({symbol})",
                summary=summary,
                source=self.source_name,
                source_id=coin_id,
                url=f"https://www.coingecko.com/en/coins/{coin_id}",
                published_date=datetime.now(timezone.utc),  # Trending is current
                author="CoinGecko",
                category=self.category,
                image_url=item.get("large") or item.get("thumb"),
                tags=["crypto", "trending", symbol.lower()],
                raw_data={
                    "market_cap_rank": item.get("market_cap_rank"),
                    "price_btc": price_btc,
                    "score": item.get("score"),
                }
            )
