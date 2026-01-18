"""Product Hunt API fetcher.

https://api.producthunt.com/v2/docs
Requires API key for full access. Limited public access available.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import os
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class ProductHuntFetcher(BaseNewsFetcher):
    """Fetcher for Product Hunt product launches."""
    
    source_name = "producthunt"
    category = "tech"
    rate_limit = 1.0
    requires_api_key = True
    
    BASE_URL = "https://api.producthunt.com/v2/api/graphql"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("PRODUCTHUNT_KEY")
        if not self.api_key:
            # Fall back to web scraping approach
            self._use_api = False
        else:
            self._use_api = True
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch product launches from Product Hunt.
        
        Keywords are used to filter by topic/category.
        """
        if self._use_api:
            async for item in self._fetch_api(keywords, max_results, days_back):
                yield item
        else:
            async for item in self._fetch_web(keywords, max_results, days_back):
                yield item
    
    async def _fetch_api(
        self,
        keywords: Optional[List[str]],
        max_results: int,
        days_back: int,
    ) -> AsyncIterator[NewsData]:
        """Fetch using official GraphQL API."""
        await self._rate_limit()
        
        # GraphQL query for posts
        query = """
        query GetPosts($first: Int!, $postedAfter: DateTime) {
            posts(first: $first, postedAfter: $postedAfter, order: VOTES) {
                edges {
                    node {
                        id
                        name
                        tagline
                        url
                        votesCount
                        commentsCount
                        createdAt
                        thumbnail {
                            url
                        }
                        topics {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        makers {
                            name
                        }
                    }
                }
            }
        }
        """
        
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        variables = {
            "first": min(max_results, 50),
            "postedAfter": from_date.isoformat(),
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        posts = data.get("data", {}).get("posts", {}).get("edges", [])
        
        for edge in posts:
            node = edge.get("node", {})
            name = node.get("name")
            if not name:
                continue
            
            # Filter by keywords if provided
            if keywords:
                topics = [t["node"]["name"].lower() for t in node.get("topics", {}).get("edges", [])]
                tagline = (node.get("tagline") or "").lower()
                combined = " ".join(topics) + " " + tagline + " " + name.lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            # Parse date
            pub_date = None
            if node.get("createdAt"):
                try:
                    pub_date = datetime.fromisoformat(node.get("createdAt").replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            # Get makers
            makers = node.get("makers", [])
            author = makers[0].get("name") if makers else None
            
            # Get topics
            topics = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
            
            yield NewsData(
                title=f"{name}: {node.get('tagline', '')}",
                summary=node.get("tagline"),
                source=self.source_name,
                source_id=node.get("id"),
                url=node.get("url"),
                published_date=pub_date,
                author=author,
                category=self.category,
                image_url=node.get("thumbnail", {}).get("url") if node.get("thumbnail") else None,
                tags=["producthunt"] + topics[:5],
                raw_data={
                    "votes_count": node.get("votesCount", 0),
                    "comments_count": node.get("commentsCount", 0),
                    "topics": topics,
                }
            )
    
    async def _fetch_web(
        self,
        keywords: Optional[List[str]],
        max_results: int,
        days_back: int,
    ) -> AsyncIterator[NewsData]:
        """Fallback: fetch from public web page."""
        await self._rate_limit()
        
        # Use the public RSS feed or front page
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.producthunt.com/feed",
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PPT-NewsFeed/1.0)"}
            )
            response.raise_for_status()
        
        # Parse as RSS
        import feedparser
        feed = feedparser.parse(response.text)
        
        count = 0
        for entry in feed.entries:
            if count >= max_results:
                break
            
            title = entry.get("title", "")
            if not title:
                continue
            
            # Filter by keywords
            if keywords:
                combined = (title + " " + entry.get("summary", "")).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    continue
            
            # Parse date
            pub_date = None
            if entry.get("published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            yield NewsData(
                title=title,
                summary=entry.get("summary"),
                source=self.source_name,
                source_id=entry.get("id", ""),
                url=entry.get("link"),
                published_date=pub_date,
                author=None,
                category=self.category,
                tags=["producthunt"],
                raw_data={}
            )
            count += 1
