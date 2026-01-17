"""Background tasks for paper fetching."""
import asyncio
from app.celery_app import celery_app
from app.core.database import async_session_maker
from app.services.fetch_service import FetchService


@celery_app.task(name="fetch_papers")
def fetch_papers_task(
    job_id: int,
    sources: list,
    keywords: list | None,
    max_results: int,
    days_back: int,
):
    """Background task to fetch papers from sources."""
    async def _run():
        async with async_session_maker() as session:
            service = FetchService(session)
            await service.run_fetch(
                job_id=job_id,
                sources=sources,
                keywords=keywords,
                max_results=max_results,
                days_back=days_back,
            )
    
    asyncio.run(_run())


@celery_app.task(name="process_digest")
def process_digest_task(digest_id: int):
    """Background task to process a digest."""
    from app.services.digest_service import DigestService
    
    async def _run():
        async with async_session_maker() as session:
            service = DigestService(session)
            await service.process_digest(digest_id)
    
    asyncio.run(_run())
