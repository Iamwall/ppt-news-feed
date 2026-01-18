"""Live Pulse service for real-time feed management.

Manages the real-time news feed with breaking news prioritization
and freshness scoring.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Callable

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.paper import Paper
from app.services.breaking_detector import BreakingNewsDetector


logger = logging.getLogger(__name__)


class LivePulseService:
    """Manages real-time feed for Live Pulse mode.

    Provides:
    - Feed retrieval sorted by breaking status + freshness
    - Breaking news alerts
    - Freshness score updates
    - Real-time update notifications
    """

    def __init__(self, db: AsyncSession):
        """Initialize service.

        Args:
            db: Database session
        """
        self.db = db
        self.breaking_detector = BreakingNewsDetector()

    async def get_feed(
        self,
        domain_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        since: Optional[datetime] = None,
        breaking_only: bool = False,
        passed_triage_only: bool = True,
        min_freshness: float = 0.0,
        validated_only: bool = False,
    ) -> List[Paper]:
        """Get live feed sorted by breaking status + freshness.

        Args:
            domain_id: Filter by domain (optional)
            limit: Maximum items to return
            offset: Pagination offset
            since: Only return items newer than this time
            breaking_only: Only return breaking news
            passed_triage_only: Only return items that passed triage
            passed_triage_only: Only return items that passed triage
            min_freshness: Minimum freshness score (0.0-1.0)
            validated_only: Only return items from validated sources

        Returns:
            List of papers sorted by importance
        """
        query = select(Paper).options(selectinload(Paper.authors))

        conditions = []

        # Filter by triage status
        # When passed_triage_only is True, we show:
        # - passed: explicitly passed triage
        # - pending: not yet triaged (default for new papers)
        # - None: legacy papers without triage status
        # We only filter out "rejected" papers
        if passed_triage_only:
            conditions.append(
                or_(
                    Paper.triage_status == "passed",
                    Paper.triage_status == "pending",
                    Paper.triage_status == None  # Include non-triaged papers
                )
            )

        # Filter by time
        if since:
            conditions.append(Paper.fetched_at >= since)

        # Filter breaking only
        if breaking_only:
            conditions.append(Paper.is_breaking == True)

        # Filter by freshness
        if min_freshness > 0:
            conditions.append(
                or_(
                    Paper.freshness_score >= min_freshness,
                    Paper.freshness_score == None
                )
            )

        # Filter by validated source
        if validated_only:
            conditions.append(Paper.is_validated_source == True)

        if conditions:
            query = query.where(and_(*conditions))

        # Sort: breaking first, then by freshness score, then by fetched time
        query = query.order_by(
            Paper.is_breaking.desc(),
            Paper.breaking_score.desc().nullslast(),
            Paper.freshness_score.desc().nullslast(),
            Paper.fetched_at.desc()
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())

        # Update freshness scores on retrieved papers
        for paper in papers:
            paper.freshness_score = self.breaking_detector.calculate_freshness(paper)

        return papers

    async def get_breaking_news(
        self,
        domain_id: Optional[str] = None,
        limit: int = 10,
        max_age_hours: int = 24,
    ) -> List[Paper]:
        """Get current breaking news.

        Args:
            domain_id: Filter by domain (optional)
            limit: Maximum items to return
            max_age_hours: Only include items from the last N hours

        Returns:
            List of breaking news papers
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        query = select(Paper).options(selectinload(Paper.authors)).where(
            and_(
                Paper.is_breaking == True,
                Paper.fetched_at >= cutoff
            )
        ).order_by(
            Paper.breaking_score.desc(),
            Paper.fetched_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_feed_stats(
        self,
        domain_id: Optional[str] = None,
        hours_back: int = 24,
    ) -> Dict[str, Any]:
        """Get statistics about the live feed.

        Args:
            domain_id: Filter by domain (optional)
            hours_back: Time window for stats

        Returns:
            Dict with feed statistics
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Total papers
        total_query = select(Paper).where(Paper.fetched_at >= cutoff)
        total_result = await self.db.execute(total_query)
        total_papers = len(list(total_result.scalars().all()))

        # Breaking papers
        breaking_query = select(Paper).where(
            and_(
                Paper.fetched_at >= cutoff,
                Paper.is_breaking == True
            )
        )
        breaking_result = await self.db.execute(breaking_query)
        breaking_count = len(list(breaking_result.scalars().all()))

        # Passed triage
        passed_query = select(Paper).where(
            and_(
                Paper.fetched_at >= cutoff,
                Paper.triage_status == "passed"
            )
        )
        passed_result = await self.db.execute(passed_query)
        passed_count = len(list(passed_result.scalars().all()))

        # Average freshness
        recent_papers = await self.get_feed(limit=50, passed_triage_only=False)
        avg_freshness = (
            sum(p.freshness_score or 0 for p in recent_papers) / len(recent_papers)
            if recent_papers else 0
        )

        return {
            "time_window_hours": hours_back,
            "total_papers": total_papers,
            "breaking_count": breaking_count,
            "passed_triage_count": passed_count,
            "avg_freshness_score": round(avg_freshness, 3),
            "breaking_rate": round(breaking_count / total_papers, 3) if total_papers else 0,
        }

    async def refresh_breaking_scores(
        self,
        domain_id: Optional[str] = None,
        hours_back: int = 48,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """Refresh breaking news and freshness scores for recent papers.

        This should be called periodically to update time-decay scores
        and re-evaluate breaking news status.

        Args:
            domain_id: Filter by domain (optional)
            hours_back: How far back to refresh
            batch_size: Process papers in batches

        Returns:
            Dict with refresh stats
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        query = select(Paper).where(Paper.fetched_at >= cutoff)
        result = await self.db.execute(query)
        papers = list(result.scalars().all())

        updated_count = 0
        new_breaking_count = 0

        for paper in papers:
            old_is_breaking = paper.is_breaking

            # Re-analyze for breaking news
            analysis = await self.breaking_detector.analyze(paper, domain_id or "news")

            # Update paper
            paper.is_breaking = analysis.is_breaking
            paper.breaking_score = analysis.score
            paper.breaking_keywords = analysis.keywords_found if analysis.keywords_found else None
            paper.freshness_score = self.breaking_detector.calculate_freshness(paper)

            self.db.add(paper)
            updated_count += 1

            if analysis.is_breaking and not old_is_breaking:
                new_breaking_count += 1

        await self.db.commit()

        return {
            "papers_updated": updated_count,
            "new_breaking": new_breaking_count,
            "time_window_hours": hours_back,
        }

    async def get_new_items_since(
        self,
        since: datetime,
        domain_id: Optional[str] = None,
        passed_triage_only: bool = True,
    ) -> List[Paper]:
        """Get new items since a specific time.

        Used for polling-based updates when WebSocket isn't available.

        Args:
            since: Get items newer than this time
            domain_id: Filter by domain (optional)
            passed_triage_only: Only include passed triage items

        Returns:
            List of new papers
        """
        conditions = [Paper.fetched_at > since]

        if passed_triage_only:
            conditions.append(
                or_(
                    Paper.triage_status == "passed",
                    Paper.triage_status == "pending",
                    Paper.triage_status == None
                )
            )

        query = select(Paper).options(selectinload(Paper.authors)).where(
            and_(*conditions)
        ).order_by(Paper.fetched_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())


class LivePulseNotifier:
    """Manages real-time notifications for Live Pulse.

    Maintains a list of connected clients (WebSocket connections)
    and broadcasts updates when new items arrive.
    """

    def __init__(self):
        """Initialize notifier."""
        # Domain -> List of callback functions
        self._subscribers: Dict[str, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []

    def subscribe(
        self,
        callback: Callable,
        domain_id: Optional[str] = None
    ):
        """Subscribe to updates.

        Args:
            callback: Async function to call with new items
            domain_id: Domain to subscribe to (None for all)
        """
        if domain_id:
            if domain_id not in self._subscribers:
                self._subscribers[domain_id] = []
            self._subscribers[domain_id].append(callback)
        else:
            self._global_subscribers.append(callback)

    def unsubscribe(
        self,
        callback: Callable,
        domain_id: Optional[str] = None
    ):
        """Unsubscribe from updates."""
        if domain_id and domain_id in self._subscribers:
            self._subscribers[domain_id] = [
                cb for cb in self._subscribers[domain_id] if cb != callback
            ]
        else:
            self._global_subscribers = [
                cb for cb in self._global_subscribers if cb != callback
            ]

    async def notify(
        self,
        paper: Paper,
        domain_id: Optional[str] = None,
        event_type: str = "new_item"
    ):
        """Notify subscribers of a new/updated item.

        Args:
            paper: Paper that was added/updated
            domain_id: Domain of the paper
            event_type: Type of event (new_item, breaking, updated)
        """
        message = {
            "type": event_type,
            "data": {
                "paper_id": paper.id,
                "title": paper.title,
                "is_breaking": paper.is_breaking,
                "breaking_score": paper.breaking_score,
                "freshness_score": paper.freshness_score,
                "url": paper.url,
                "source": paper.source,
                "published_date": paper.published_date.isoformat() if paper.published_date else None,
                "fetched_at": paper.fetched_at.isoformat() if paper.fetched_at else None,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Notify domain-specific subscribers
        if domain_id and domain_id in self._subscribers:
            for callback in self._subscribers[domain_id]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")

        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error notifying global subscriber: {e}")

    async def notify_breaking(self, paper: Paper, domain_id: Optional[str] = None):
        """Send breaking news alert."""
        await self.notify(paper, domain_id, "breaking")


# Global notifier instance
live_pulse_notifier = LivePulseNotifier()
