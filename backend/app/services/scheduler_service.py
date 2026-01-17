"""Scheduler service for automated digest generation.

Uses APScheduler for cron-based scheduling of digest generation.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None
    CronTrigger = None

from app.models.digest_schedule import DigestSchedule, ScheduledDigest
from app.models.digest import Digest, DigestStatus
from app.models.paper import Paper
from app.models.domain_config import DomainConfig
from app.services.domain_service import DomainService
from app.services.digest_service import DigestService
from app.ai.topic_clusterer import TopicClusterer


logger = logging.getLogger(__name__)


class DigestScheduler:
    """Manages scheduled digest generation.

    Uses APScheduler to run cron-based jobs that automatically
    generate digests based on configured schedules.
    """

    def __init__(self):
        """Initialize the scheduler."""
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._started = False

    @property
    def is_available(self) -> bool:
        """Check if APScheduler is available."""
        return APSCHEDULER_AVAILABLE

    @property
    def scheduler(self) -> Optional[AsyncIOScheduler]:
        """Get or create the scheduler instance."""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not installed. Scheduled digests disabled.")
            return None

        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(
                jobstores={"default": MemoryJobStore()},
                job_defaults={
                    "coalesce": True,
                    "max_instances": 1,
                    "misfire_grace_time": 3600,  # 1 hour grace period
                }
            )
        return self._scheduler

    async def start(self, db_session_maker) -> bool:
        """Start the scheduler and load all active schedules.

        Args:
            db_session_maker: Async session maker for database access

        Returns:
            True if started successfully
        """
        if not self.is_available:
            logger.warning("Cannot start scheduler: APScheduler not installed")
            return False

        if self._started:
            logger.info("Scheduler already started")
            return True

        try:
            # Store session maker for job execution
            self._db_session_maker = db_session_maker

            # Load and register all active schedules
            async with db_session_maker() as session:
                schedules = await self._get_active_schedules(session)
                for schedule in schedules:
                    self._add_schedule_job(schedule)

            # Start the scheduler
            self.scheduler.start()
            self._started = True
            logger.info(f"Scheduler started with {len(schedules)} active schedules")
            return True

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False

    async def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Scheduler stopped")

    def _add_schedule_job(self, schedule: DigestSchedule):
        """Add a schedule job to the scheduler."""
        if not self.scheduler:
            return

        job_id = f"digest_schedule_{schedule.id}"

        try:
            # Parse cron expression
            cron_parts = schedule.cron_expression.split()
            if len(cron_parts) != 5:
                logger.error(f"Invalid cron expression for schedule {schedule.id}: {schedule.cron_expression}")
                return

            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4],
                timezone=schedule.timezone,
            )

            # Add job
            self.scheduler.add_job(
                self._execute_scheduled_digest,
                trigger=trigger,
                args=[schedule.id],
                id=job_id,
                replace_existing=True,
                name=f"Scheduled Digest: {schedule.name}",
            )

            logger.info(f"Added schedule job: {job_id} ({schedule.cron_expression})")

        except Exception as e:
            logger.error(f"Failed to add schedule job {schedule.id}: {e}")

    def _remove_schedule_job(self, schedule_id: int):
        """Remove a schedule job from the scheduler."""
        if not self.scheduler:
            return

        job_id = f"digest_schedule_{schedule_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule job: {job_id}")
        except Exception:
            pass  # Job may not exist

    async def _execute_scheduled_digest(self, schedule_id: int):
        """Execute a scheduled digest generation.

        This is called by APScheduler when a schedule triggers.
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Executing scheduled digest for schedule {schedule_id}")

        async with self._db_session_maker() as session:
            try:
                # Get schedule
                result = await session.execute(
                    select(DigestSchedule).where(DigestSchedule.id == schedule_id)
                )
                schedule = result.scalar_one_or_none()

                if not schedule or not schedule.is_active:
                    logger.warning(f"Schedule {schedule_id} not found or inactive")
                    return

                # Get domain config
                domain_service = DomainService(session)
                domain_config = await domain_service.get_domain_config(schedule.domain_id)

                # Get papers from lookback period
                papers = await self._get_papers_for_schedule(session, schedule)

                if not papers:
                    logger.info(f"No papers found for schedule {schedule_id}")
                    schedule.last_run_at = start_time
                    schedule.last_error = "No papers found in lookback period"
                    await session.commit()
                    return

                # Create digest
                digest = await self._create_scheduled_digest(
                    session, schedule, papers, domain_config
                )

                # Record scheduled digest
                scheduled_digest = ScheduledDigest(
                    schedule_id=schedule.id,
                    digest_id=digest.id,
                    papers_considered=len(papers),
                    papers_included=len(digest.digest_papers),
                    triggered_at=start_time,
                    completed_at=datetime.now(timezone.utc),
                    generation_time_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
                )
                session.add(scheduled_digest)

                # Update schedule
                schedule.last_run_at = start_time
                schedule.run_count += 1
                schedule.last_error = None

                # Calculate next run time
                if self.scheduler:
                    job = self.scheduler.get_job(f"digest_schedule_{schedule_id}")
                    if job:
                        schedule.next_run_at = job.next_run_time

                await session.commit()
                logger.info(f"Scheduled digest completed: {digest.id} ({len(papers)} papers)")

            except Exception as e:
                logger.error(f"Failed to execute scheduled digest {schedule_id}: {e}")
                import traceback
                traceback.print_exc()

                # Update schedule with error
                try:
                    result = await session.execute(
                        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
                    )
                    schedule = result.scalar_one_or_none()
                    if schedule:
                        schedule.last_run_at = start_time
                        schedule.last_error = str(e)[:500]
                        await session.commit()
                except Exception:
                    pass

    async def _get_active_schedules(self, session: AsyncSession) -> List[DigestSchedule]:
        """Get all active schedules from database."""
        result = await session.execute(
            select(DigestSchedule).where(DigestSchedule.is_active == True)
        )
        return list(result.scalars().all())

    async def _get_papers_for_schedule(
        self,
        session: AsyncSession,
        schedule: DigestSchedule
    ) -> List[Paper]:
        """Get papers for a schedule based on lookback period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=schedule.lookback_hours)

        query = select(Paper).where(
            Paper.fetched_at >= cutoff
        )

        # Filter by triage status if enabled
        if schedule.only_passed_triage:
            query = query.where(Paper.triage_status == "passed")

        # Filter by minimum triage score
        if schedule.min_triage_score:
            query = query.where(
                (Paper.triage_score >= schedule.min_triage_score) |
                (Paper.triage_score == None)  # Include non-triaged papers
            )

        # Order by quality and recency
        query = query.order_by(
            Paper.triage_score.desc().nullsfirst(),
            Paper.fetched_at.desc()
        ).limit(schedule.max_items * 2)  # Get more than needed for clustering

        result = await session.execute(query)
        return list(result.scalars().all())

    async def _create_scheduled_digest(
        self,
        session: AsyncSession,
        schedule: DigestSchedule,
        papers: List[Paper],
        domain_config: Optional[DomainConfig]
    ) -> Digest:
        """Create a digest from scheduled papers."""
        # Create digest
        digest_name = f"{schedule.name} - {datetime.now().strftime('%Y-%m-%d')}"
        digest = Digest(
            name=digest_name,
            status=DigestStatus.PENDING,
            ai_provider=schedule.ai_provider,
            ai_model=schedule.ai_model or "gemini-1.5-pro",
        )
        session.add(digest)
        await session.commit()
        await session.refresh(digest)

        # Cluster topics if enabled
        if schedule.cluster_topics:
            clusterer = TopicClusterer(
                provider=schedule.ai_provider,
                model=schedule.ai_model,
                db=session
            )
            await clusterer.cluster_and_save(
                papers=papers[:schedule.max_items],
                digest_id=digest.id,
                domain_config=domain_config,
                max_clusters=5,
                top_picks_count=schedule.top_picks_count,
            )

        # Add papers to digest
        from app.models.digest import DigestPaper
        for i, paper in enumerate(papers[:schedule.max_items]):
            digest_paper = DigestPaper(
                digest_id=digest.id,
                paper_id=paper.id,
                order=i
            )
            session.add(digest_paper)

        # Process digest with AI (generate summaries, etc.)
        digest_service = DigestService(session)
        await digest_service.process_digest(digest.id)

        await session.commit()
        return digest

    async def add_schedule(
        self,
        session: AsyncSession,
        schedule: DigestSchedule
    ):
        """Add a new schedule and register it with the scheduler."""
        session.add(schedule)
        await session.commit()
        await session.refresh(schedule)

        if schedule.is_active:
            self._add_schedule_job(schedule)

        return schedule

    async def update_schedule(
        self,
        session: AsyncSession,
        schedule: DigestSchedule
    ):
        """Update a schedule and refresh its scheduler job."""
        # Remove old job
        self._remove_schedule_job(schedule.id)

        await session.commit()

        # Add new job if active
        if schedule.is_active:
            self._add_schedule_job(schedule)

    async def delete_schedule(
        self,
        session: AsyncSession,
        schedule_id: int
    ):
        """Delete a schedule and remove its scheduler job."""
        self._remove_schedule_job(schedule_id)

        result = await session.execute(
            select(DigestSchedule).where(DigestSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if schedule:
            await session.delete(schedule)
            await session.commit()

    async def trigger_now(
        self,
        session: AsyncSession,
        schedule_id: int
    ) -> Optional[int]:
        """Manually trigger a schedule immediately.

        Returns:
            Digest ID if successful, None otherwise
        """
        result = await session.execute(
            select(DigestSchedule).where(DigestSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            return None

        # Execute immediately (not through scheduler)
        await self._execute_scheduled_digest(schedule_id)

        # Return the latest digest ID
        result = await session.execute(
            select(ScheduledDigest)
            .where(ScheduledDigest.schedule_id == schedule_id)
            .order_by(ScheduledDigest.triggered_at.desc())
            .limit(1)
        )
        scheduled = result.scalar_one_or_none()
        return scheduled.digest_id if scheduled else None


# Global scheduler instance
digest_scheduler = DigestScheduler()


async def start_scheduler(db_session_maker):
    """Start the global scheduler."""
    return await digest_scheduler.start(db_session_maker)


async def stop_scheduler():
    """Stop the global scheduler."""
    await digest_scheduler.stop()
