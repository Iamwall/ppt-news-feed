"""RSS feed fetchers for Nature and Science journals."""
from datetime import datetime, timedelta
from typing import Optional, List, AsyncIterator
from email.utils import parsedate_to_datetime
import httpx
import feedparser

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class RSSFetcher(BaseFetcher):
    """Base RSS feed fetcher."""
    
    source_name = "rss"
    rate_limit = 1.0
    feed_url: str = ""
    journal_name: str = ""
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from RSS feed."""
        
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

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(self.feed_url, timeout=30.0)
            response.raise_for_status()

        feed = feedparser.parse(response.content)
        return feed.entries
    
    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse an RSS entry. Override in subclasses."""
        
        title = entry.get("title", "Untitled")
        
        # Get link
        link = entry.get("link", "")
        
        # Get abstract from summary or description
        abstract = entry.get("summary") or entry.get("description")
        
        # Extract DOI from link if possible
        doi = None
        if "doi.org" in link:
            doi = link.split("doi.org/")[-1]
        
        # Parse date
        pub_date = None
        if "published_parsed" in entry and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif "updated_parsed" in entry and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])
        
        # Authors
        authors = []
        author_detail = entry.get("author_detail", {})
        if author_detail.get("name"):
            authors.append(AuthorData(name=author_detail["name"]))
        elif entry.get("author"):
            for name in entry["author"].split(","):
                authors.append(AuthorData(name=name.strip()))
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=link,
            journal=self.journal_name,
            doi=doi,
            url=link,
            published_date=pub_date,
            is_peer_reviewed=True,
            is_preprint=False,
        )


class NatureRSSFetcher(RSSFetcher):
    """Fetcher for Nature journal RSS feed."""
    
    source_name = "nature_rss"
    feed_url = "https://www.nature.com/nature.rss"
    journal_name = "Nature"
    
    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse Nature RSS entry with specific handling."""
        paper = super()._parse_entry(entry)
        
        if paper:
            # Nature specific: extract DOI from dc:identifier if available
            if not paper.doi:
                identifier = entry.get("dc_identifier") or entry.get("id", "")
                if "doi:" in identifier.lower():
                    paper.doi = identifier.split("doi:")[-1].strip()
            
            # Set high impact factor for Nature
            paper.journal_impact_factor = 64.8  # Approximate
        
        return paper


class ScienceRSSFetcher(RSSFetcher):
    """Fetcher for Science journal RSS feed."""

    source_name = "science_rss"
    feed_url = "https://feeds.science.org/rss/science.xml"
    journal_name = "Science"
    
    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse Science RSS entry with specific handling."""
        paper = super()._parse_entry(entry)
        
        if paper:
            # Set high impact factor for Science
            paper.journal_impact_factor = 56.9  # Approximate
        
        return paper


class CellRSSFetcher(RSSFetcher):
    """Fetcher for Cell journal RSS feed."""

    source_name = "cell_rss"
    feed_url = "https://www.cell.com/cell/rss/current.xml"
    journal_name = "Cell"

    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse Cell RSS entry."""
        paper = super()._parse_entry(entry)

        if paper:
            paper.journal_impact_factor = 66.8  # Approximate

        return paper


class PLOSBiologyRSSFetcher(RSSFetcher):
    """Fetcher for PLOS Biology journal RSS feed."""

    source_name = "plos_biology_rss"
    feed_url = "https://journals.plos.org/plosbiology/feed/atom"
    journal_name = "PLOS Biology"

    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse PLOS Biology RSS entry."""
        paper = super()._parse_entry(entry)

        if paper:
            paper.journal_impact_factor = 9.8  # Approximate

        return paper


class LancetRSSFetcher(RSSFetcher):
    """Fetcher for The Lancet journal RSS feed."""

    source_name = "lancet_rss"
    feed_url = "https://www.thelancet.com/rssfeed/lancet_current.xml"
    journal_name = "The Lancet"

    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse Lancet RSS entry."""
        paper = super()._parse_entry(entry)

        if paper:
            paper.journal_impact_factor = 202.7  # Very high impact

        return paper


class NEJMRSSFetcher(RSSFetcher):
    """Fetcher for New England Journal of Medicine RSS feed."""

    source_name = "nejm_rss"
    feed_url = "https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm"
    journal_name = "New England Journal of Medicine"

    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse NEJM RSS entry."""
        paper = super()._parse_entry(entry)

        if paper:
            paper.journal_impact_factor = 176.1  # Very high impact

        return paper


class BMJRSSFetcher(RSSFetcher):
    """Fetcher for BMJ (British Medical Journal) RSS feed."""

    source_name = "bmj_rss"
    feed_url = "https://www.bmj.com/rss/recent.xml"
    journal_name = "BMJ"

    def _parse_entry(self, entry: dict) -> Optional[PaperData]:
        """Parse BMJ RSS entry."""
        paper = super()._parse_entry(entry)

        if paper:
            paper.journal_impact_factor = 93.6  # High impact

        return paper
