"""PRAW Reddit wrapper for authenticated access.

https://praw.readthedocs.io/
Requires Reddit API credentials.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import asyncio

from app.fetchers.base import BaseNewsFetcher, NewsData


class PRAWFetcher(BaseNewsFetcher):
    """Enhanced Reddit fetcher using PRAW library."""
    
    source_name = "praw"
    category = "news"
    rate_limit = 1.0
    requires_api_key = True
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "PPT-NewsFeed/1.0",
    ):
        super().__init__()
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent
        
        if not self.client_id or not self.client_secret:
            raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch posts from Reddit using PRAW."""
        try:
            import praw
        except ImportError:
            raise ImportError("praw not installed. Run: pip install praw")
        
        await self._rate_limit()
        
        # Initialize Reddit
        reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )
        
        subreddits = keywords if keywords else ["technology", "programming", "science"]
        
        loop = asyncio.get_event_loop()
        
        for subreddit_name in subreddits[:5]:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Get hot posts
                posts = await loop.run_in_executor(
                    None,
                    lambda: list(subreddit.hot(limit=max_results // len(subreddits)))
                )
                
                for post in posts:
                    yield NewsData(
                        title=post.title,
                        summary=post.selftext[:500] if post.selftext else None,
                        source=self.source_name,
                        source_id=post.id,
                        url=f"https://reddit.com{post.permalink}",
                        published_date=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                        author=str(post.author) if post.author else None,
                        category=self.category,
                        image_url=post.thumbnail if post.thumbnail.startswith("http") else None,
                        tags=["reddit", subreddit_name],
                        raw_data={
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "upvote_ratio": post.upvote_ratio,
                        }
                    )
            except Exception as e:
                print(f"PRAW error for r/{subreddit_name}: {e}")
                continue
