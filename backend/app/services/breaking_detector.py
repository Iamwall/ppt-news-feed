"""Breaking news detection service.

Detects breaking/urgent news based on content signals and keywords.
"""
import math
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Set
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper


logger = logging.getLogger(__name__)


@dataclass
class BreakingAnalysis:
    """Result of breaking news analysis."""
    is_breaking: bool
    score: float  # 0.0-1.0 urgency score
    keywords_found: List[str]
    signals: Dict[str, float]  # Signal name -> contribution


class BreakingNewsDetector:
    """Detects breaking/urgent news based on content signals.

    Analyzes paper content for volatility keywords, recency,
    and other signals to determine if it should be flagged as breaking news.
    """

    # Domain-specific volatility keywords
    BREAKING_KEYWORDS: Dict[str, List[str]] = {
        "news": [
            "breaking", "just in", "developing", "urgent", "alert",
            "exclusive", "confirmed", "announced", "revealed",
            "emergency", "crisis", "unprecedented"
        ],
        "business": [
            "crash", "surge", "plunge", "bankruptcy", "merger", "acquisition",
            "sec", "fed", "layoffs", "ipo", "earnings miss", "earnings beat",
            "stock split", "dividend cut", "recall", "fraud", "scandal"
        ],
        "tech": [
            "leak", "breach", "hack", "outage", "shutdown", "launch",
            "vulnerability", "zero-day", "exploit", "ransomware",
            "ai breakthrough", "acquisition", "layoffs", "released"
        ],
        "health": [
            "outbreak", "pandemic", "epidemic", "emergency", "recall",
            "fda approval", "clinical trial", "vaccine", "mutation",
            "death toll", "hospitalization", "new variant", "breakthrough"
        ],
        "science": [
            "discovery", "breakthrough", "retraction", "confirmed",
            "first ever", "never before", "revolutionary", "groundbreaking",
            "major finding", "landmark study", "Nobel"
        ],
    }

    # Universal high-urgency keywords (apply to all domains)
    UNIVERSAL_KEYWORDS: List[str] = [
        "breaking", "urgent", "emergency", "crisis", "just announced",
        "confirmed dead", "war", "attack", "explosion", "earthquake",
        "tsunami", "hurricane", "wildfire", "mass shooting"
    ]

    # Signal weights for scoring
    SIGNAL_WEIGHTS: Dict[str, float] = {
        "keyword_match": 0.35,
        "universal_keyword": 0.25,
        "recency": 0.25,
        "title_urgency": 0.15,
    }

    # Recency thresholds (hours)
    RECENCY_THRESHOLD_VERY_FRESH = 2  # < 2 hours = very fresh
    RECENCY_THRESHOLD_FRESH = 6  # < 6 hours = fresh
    RECENCY_THRESHOLD_RECENT = 24  # < 24 hours = recent

    def __init__(self, breaking_threshold: float = 0.5):
        """Initialize detector.

        Args:
            breaking_threshold: Minimum score to flag as breaking (default 0.5)
        """
        self.breaking_threshold = breaking_threshold

    async def analyze(
        self,
        paper: Paper,
        domain: str = "news"
    ) -> BreakingAnalysis:
        """Analyze if paper should be flagged as breaking news.

        Args:
            paper: Paper to analyze
            domain: Domain context for keyword selection

        Returns:
            BreakingAnalysis with results
        """
        signals = {}
        keywords_found = []
        total_score = 0.0

        text = f"{paper.title or ''} {paper.abstract or ''}".lower()

        # Check domain-specific keywords
        domain_keywords = self.BREAKING_KEYWORDS.get(domain, [])
        for keyword in domain_keywords:
            if keyword.lower() in text:
                keywords_found.append(keyword)

        if keywords_found:
            # More keywords = higher score, but cap at weight
            keyword_score = min(len(keywords_found) * 0.15, self.SIGNAL_WEIGHTS["keyword_match"])
            signals["keyword_match"] = keyword_score
            total_score += keyword_score

        # Check universal keywords
        universal_found = []
        for keyword in self.UNIVERSAL_KEYWORDS:
            if keyword.lower() in text:
                universal_found.append(keyword)
                keywords_found.append(f"[URGENT] {keyword}")

        if universal_found:
            universal_score = min(len(universal_found) * 0.1, self.SIGNAL_WEIGHTS["universal_keyword"])
            signals["universal_keyword"] = universal_score
            total_score += universal_score

        # Check recency
        recency_score = self._calculate_recency_score(paper)
        if recency_score > 0:
            signals["recency"] = recency_score
            total_score += recency_score

        # Check title urgency patterns
        title_urgency = self._analyze_title_urgency(paper.title or "")
        if title_urgency > 0:
            signals["title_urgency"] = title_urgency
            total_score += title_urgency

        # Determine if breaking
        is_breaking = total_score >= self.breaking_threshold

        return BreakingAnalysis(
            is_breaking=is_breaking,
            score=min(total_score, 1.0),
            keywords_found=keywords_found,
            signals=signals
        )

    async def analyze_and_update(
        self,
        paper: Paper,
        domain: str = "news",
        db: Optional[AsyncSession] = None
    ) -> BreakingAnalysis:
        """Analyze paper and update its breaking news fields.

        Args:
            paper: Paper to analyze
            domain: Domain context
            db: Database session for saving (optional)

        Returns:
            BreakingAnalysis with results
        """
        analysis = await self.analyze(paper, domain)

        # Update paper
        paper.is_breaking = analysis.is_breaking
        paper.breaking_score = analysis.score
        paper.breaking_keywords = analysis.keywords_found if analysis.keywords_found else None

        # Also update freshness score
        paper.freshness_score = self.calculate_freshness(paper)

        if db:
            db.add(paper)
            await db.commit()

        return analysis

    async def analyze_batch(
        self,
        papers: List[Paper],
        domain: str = "news",
        db: Optional[AsyncSession] = None
    ) -> List[BreakingAnalysis]:
        """Analyze multiple papers for breaking news.

        Args:
            papers: Papers to analyze
            domain: Domain context
            db: Database session (optional)

        Returns:
            List of BreakingAnalysis results
        """
        results = []

        for paper in papers:
            if db:
                analysis = await self.analyze_and_update(paper, domain, db)
            else:
                analysis = await self.analyze(paper, domain)
            results.append(analysis)

        return results

    def _calculate_recency_score(self, paper: Paper) -> float:
        """Calculate recency contribution to breaking score."""
        # Try published_at first, then published_date, then fetched_at
        pub_time = paper.published_at or paper.published_date or paper.fetched_at

        if not pub_time:
            return 0.0

        # Make pub_time timezone-aware if it isn't
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        hours_old = (now - pub_time).total_seconds() / 3600

        if hours_old < self.RECENCY_THRESHOLD_VERY_FRESH:
            # Very fresh: full recency weight
            return self.SIGNAL_WEIGHTS["recency"]
        elif hours_old < self.RECENCY_THRESHOLD_FRESH:
            # Fresh: 75% of weight
            return self.SIGNAL_WEIGHTS["recency"] * 0.75
        elif hours_old < self.RECENCY_THRESHOLD_RECENT:
            # Recent: 50% of weight
            return self.SIGNAL_WEIGHTS["recency"] * 0.5
        else:
            # Old: minimal contribution
            return self.SIGNAL_WEIGHTS["recency"] * 0.1

    def _analyze_title_urgency(self, title: str) -> float:
        """Analyze title for urgency patterns."""
        title_lower = title.lower()
        score = 0.0
        weight = self.SIGNAL_WEIGHTS["title_urgency"]

        # Check for urgency patterns
        urgency_patterns = [
            r"^breaking:",
            r"^urgent:",
            r"^alert:",
            r"^just in:",
            r"^developing:",
            r"^exclusive:",
            r"\[breaking\]",
            r"\[urgent\]",
            r"!$",  # Ends with exclamation
            r"!!!",  # Multiple exclamations
        ]

        for pattern in urgency_patterns:
            if re.search(pattern, title_lower):
                score += weight * 0.5
                break

        # Check for ALL CAPS words (often indicates urgency)
        words = title.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 2]
        if len(caps_words) >= 2:
            score += weight * 0.3

        return min(score, weight)

    def calculate_freshness(self, paper: Paper) -> float:
        """Calculate freshness score with exponential decay.

        Returns:
            Score from 0.0 (old) to 1.0 (brand new)
        """
        pub_time = paper.published_at or paper.published_date or paper.fetched_at

        if not pub_time:
            return 0.5  # Default for unknown

        # Make timezone-aware
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        hours_old = (now - pub_time).total_seconds() / 3600

        # Exponential decay with 24-hour half-life
        # At 0 hours: 1.0, at 24 hours: 0.5, at 48 hours: 0.25
        half_life_hours = 24
        return math.exp(-0.693 * hours_old / half_life_hours)

    async def refresh_freshness_scores(
        self,
        papers: List[Paper],
        db: Optional[AsyncSession] = None
    ):
        """Refresh freshness scores for papers.

        Called periodically to update time-decay scores.
        """
        for paper in papers:
            paper.freshness_score = self.calculate_freshness(paper)

        if db:
            for paper in papers:
                db.add(paper)
            await db.commit()


# Convenience function
async def detect_breaking_news(
    papers: List[Paper],
    domain: str = "news",
    db: Optional[AsyncSession] = None,
    threshold: float = 0.5
) -> Dict:
    """Analyze papers for breaking news.

    Returns:
        Dict with stats: {"total", "breaking_count", "results"}
    """
    detector = BreakingNewsDetector(breaking_threshold=threshold)
    results = await detector.analyze_batch(papers, domain, db)

    breaking_count = sum(1 for r in results if r.is_breaking)

    return {
        "total": len(results),
        "breaking_count": breaking_count,
        "breaking_rate": breaking_count / len(results) if results else 0,
        "results": results,
    }
