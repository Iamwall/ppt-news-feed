"""Reddit API fetcher using PRAW-style direct API access.

https://www.reddit.com/dev/api/
Can work without API key for public subreddits via JSON endpoints.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class RedditFetcher(BaseNewsFetcher):
    """Fetcher for Reddit using public JSON endpoints."""
    
    source_name = "reddit"
    category = "general"
    rate_limit = 0.5  # Reddit is strict: ~60 requests/min
    requires_api_key = False  # Can use public JSON endpoints
    
    BASE_URL = "https://www.reddit.com"
    
    # Default subreddits for different categories
    DEFAULT_SUBREDDITS = {
        "tech": ["technology", "programming", "webdev", "MachineLearning"],
        "news": ["news", "worldnews"],
        "science": ["science", "askscience"],
        "finance": ["wallstreetbets", "stocks", "CryptoCurrency"],
    }
    
    def __init__(self, subreddits: Optional[List[str]] = None):
        super().__init__()
        self.subreddits = subreddits or ["technology", "news", "science"]
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch top posts from Reddit.
        
        Uses public JSON endpoints (no authentication required).
        """
        headers = {
            "User-Agent": "PPT-NewsFeed/1.0 (Research Project)"
        }
        
        results_per_sub = max_results // len(self.subreddits) + 1
        
        async with httpx.AsyncClient() as client:
            for subreddit in self.subreddits:
                await self._rate_limit()
                
                try:
                    # Use JSON endpoint for public access
                    url = f"{self.BASE_URL}/r/{subreddit}/hot.json"
                    params = {"limit": min(results_per_sub, 100)}
                    
                    if keywords:
                        # Use search within subreddit
                        url = f"{self.BASE_URL}/r/{subreddit}/search.json"
                        params = {
                            "q": " OR ".join(keywords),
                            "restrict_sr": "on",
                            "sort": "new",
                            "limit": min(results_per_sub, 100),
                        }
                    
                    response = await client.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=30.0,
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                except Exception as e:
                    print(f"Error fetching r/{subreddit}: {e}")
                    continue
                
                posts = data.get("data", {}).get("children", [])
                
                for post_data in posts:
                    post = post_data.get("data", {})
                    
                    if not post.get("title"):
                        continue
                    
                    # Parse created time
                    created_utc = post.get("created_utc")
                    pub_date = None
                    if created_utc:
                        pub_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                    
                    # Build summary
                    selftext = post.get("selftext", "")
                    if selftext and len(selftext) > 500:
                        selftext = selftext[:500] + "..."
                    
                    yield NewsData(
                        title=post.get("title"),
                        summary=selftext or None,
                        source=self.source_name,
                        source_id=post.get("id"),
                        url=f"https://reddit.com{post.get('permalink', '')}",
                        published_date=pub_date,
                        author=post.get("author"),
                        category=self.category,
                        image_url=post.get("thumbnail") if post.get("thumbnail", "").startswith("http") else None,
                        tags=["reddit", subreddit],
                        raw_data={
                            "subreddit": subreddit,
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "upvote_ratio": post.get("upvote_ratio", 0),
                            "is_self": post.get("is_self", False),
                        }
                    )
