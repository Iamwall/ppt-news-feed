"""Custom RSS fetcher for user-defined sources."""
from datetime import datetime, timedelta
from typing import Optional, List, AsyncIterator
import httpx
import feedparser

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class CustomRSSFetcher(BaseFetcher):
    """Fetcher for custom RSS feeds defined by users."""

    rate_limit = 1.0

    def __init__(
        self,
        source_id: str,
        feed_url: str,
        source_name: str,
        is_validated: bool = False,
        is_peer_reviewed: bool = False,
    ):
        """Initialize custom RSS fetcher.

        Args:
            source_id: Unique source identifier (e.g., 'custom_tech_techcrunch')
            feed_url: URL of the RSS feed
            source_name: Human-readable name of the source
            is_validated: Whether this is a validated source
            is_peer_reviewed: Whether content is peer-reviewed
        """
        super().__init__()
        self.source_id = source_id
        self.feed_url = feed_url
        self.source_name_display = source_name
        self.is_validated = is_validated
        self.is_peer_reviewed = is_peer_reviewed

    @property
    def source_name(self) -> str:
        return self.source_id

    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from custom RSS feed."""

        # Fetch and parse feed
        entries = await self._fetch_feed()

        # Calculate date threshold
        from_date = datetime.now() - timedelta(days=days_back)

        count = 0
        for entry in entries:
            if count >= max_results:
                break

            paper = self._parse_entry(entry)
            if not paper:
                continue

            # Filter by date
            if paper.published_date and paper.published_date < from_date:
                continue

            # Filter by keywords if provided
            if keywords:
                text = f"{paper.title} {paper.abstract or ''}".lower()
                if not any(kw.lower() in text for kw in keywords):
                    continue

            yield paper
            count += 1

    async def _fetch_feed(self) -> List[dict]:
        """Fetch and parse the RSS feed."""
        await self._rate_limit()

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ScienceDigest/1.0; +https://example.com)"
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                self.feed_url,
                timeout=30.0,
                headers=headers,
            )
            response.raise_for_status()

        feed = feedparser.parse(response.content)
        return feed.entries

    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse an RSS entry into PaperData."""

        title = entry.get("title", "").strip()
        if not title:
            return None

        # Get link
        link = entry.get("link", "")

        # Get abstract/summary
        abstract = None
        if entry.get("summary"):
            abstract = entry.get("summary")
        elif entry.get("description"):
            abstract = entry.get("description")
        elif entry.get("content"):
            # Some feeds use content array
            content = entry.get("content", [])
            if content and isinstance(content, list):
                abstract = content[0].get("value", "")

        # Clean up abstract (remove HTML tags for display)
        if abstract:
            import re
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = abstract.strip()[:2000]  # Limit length

        # Parse date
        pub_date = None
        if "published_parsed" in entry and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif "updated_parsed" in entry and entry.updated_parsed:
            try:
                pub_date = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass

        # Authors
        authors = []
        if entry.get("author"):
            author_str = entry.get("author", "")
            if "," in author_str:
                for name in author_str.split(","):
                    name = name.strip()
                    if name:
                        authors.append(AuthorData(name=name))
            elif author_str:
                authors.append(AuthorData(name=author_str))
        elif entry.get("authors"):
            for author in entry.get("authors", []):
                if isinstance(author, dict) and author.get("name"):
                    authors.append(AuthorData(name=author["name"]))
                elif isinstance(author, str):
                    authors.append(AuthorData(name=author))

        # Generate unique source_id from link
        entry_id = entry.get("id") or link or title

        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_id,
            source_id=entry_id,
            journal=self.source_name_display,
            doi=None,
            url=link,
            published_date=pub_date,
            is_peer_reviewed=self.is_peer_reviewed,
            is_preprint=False,
        )
