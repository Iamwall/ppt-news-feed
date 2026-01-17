"""Service for fetching papers from multiple sources."""
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.paper import Paper, Author
from app.models.fetch_job import FetchJob, FetchStatus
from app.fetchers import get_fetcher, PaperData


class FetchService:
    """Service for managing paper fetch operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def start_fetch(
        self,
        sources: List[str],
        keywords: Optional[List[str]],
        max_results: int,
        days_back: int,
    ) -> FetchJob:
        """Create a new fetch job."""
        job = FetchJob(
            sources=sources,
            keywords=keywords,
            max_results=max_results,
            days_back=days_back,
            status=FetchStatus.PENDING,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def run_fetch(
        self,
        job_id: int,
        sources: List[str],
        keywords: Optional[List[str]],
        max_results: int,
        days_back: int,
    ):
        """Execute the fetch operation."""
        # Get job
        result = await self.db.execute(select(FetchJob).where(FetchJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            return
        
        job.status = FetchStatus.RUNNING
        await self.db.commit()
        
        errors = []
        papers_fetched = 0
        papers_new = 0
        papers_updated = 0
        
        try:
            # Fetch from each source
            for i, source in enumerate(sources):
                job.current_source = source
                job.progress = int((i / len(sources)) * 100)
                await self.db.commit()

                try:
                    fetcher = get_fetcher(source)
                    print(f"[Fetch] Starting fetch from {source}...")

                    # Wrap fetch in a timeout to prevent hanging on slow sources
                    try:
                        async with asyncio.timeout(90):  # 90 second max per source
                            async for paper_data in fetcher.fetch(
                                keywords=keywords,
                                max_results=max_results // len(sources),
                                days_back=days_back,
                            ):
                                papers_fetched += 1
                                print(f"[Fetch] Fetched paper: {paper_data.title[:50]}...")

                                # Check if paper exists (by DOI or source_id)
                                existing = await self._find_existing_paper(paper_data)

                                if existing:
                                    # Update existing paper
                                    await self._update_paper(existing, paper_data)
                                    papers_updated += 1
                                    print(f"[Fetch] Updated existing paper (ID: {existing.id})")
                                else:
                                    # Create new paper
                                    new_paper = await self._create_paper(paper_data)
                                    papers_new += 1
                                    print(f"[Fetch] Created new paper (ID: {new_paper.id})")
                    except asyncio.TimeoutError:
                        error_msg = f"{source}: Timed out after 90 seconds (skipping)"
                        print(f"[Fetch Warning] {error_msg}")
                        errors.append(error_msg)

                except Exception as e:
                    error_msg = f"{source}: {str(e)}"
                    print(f"[Fetch Error] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    errors.append(error_msg)
            
            # Update job status
            job.status = FetchStatus.COMPLETED
            job.papers_fetched = papers_fetched
            job.papers_new = papers_new
            job.papers_updated = papers_updated
            job.errors = errors if errors else None
            job.completed_at = datetime.now(timezone.utc)
            job.progress = 100
            job.current_source = None
            
        except Exception as e:
            job.status = FetchStatus.FAILED
            job.errors = [str(e)]
            job.completed_at = datetime.now(timezone.utc)
        
        await self.db.commit()
    
    async def _find_existing_paper(self, paper_data: PaperData) -> Optional[Paper]:
        """Find existing paper by DOI or source ID."""
        # Try DOI first
        if paper_data.doi:
            result = await self.db.execute(
                select(Paper).where(Paper.doi == paper_data.doi)
            )
            paper = result.scalar_one_or_none()
            if paper:
                return paper
        
        # Try source + source_id
        result = await self.db.execute(
            select(Paper).where(
                Paper.source == paper_data.source,
                Paper.source_id == paper_data.source_id
            )
        )
        return result.scalar_one_or_none()
    
    async def _create_paper(self, paper_data: PaperData) -> Paper:
        """Create a new paper from fetched data."""
        try:
            paper = Paper(
                title=paper_data.title,
                abstract=paper_data.abstract,
                journal=paper_data.journal,
                doi=paper_data.doi,
                url=paper_data.url,
                source=paper_data.source,
                source_id=paper_data.source_id,
                published_date=paper_data.published_date,
                citations=paper_data.citations,
                influential_citations=paper_data.influential_citations,
                altmetric_score=paper_data.altmetric_score,
                journal_impact_factor=paper_data.journal_impact_factor,
                is_peer_reviewed=paper_data.is_peer_reviewed,
                is_preprint=paper_data.is_preprint,
            )

            # Add authors
            for author_data in paper_data.authors:
                author = Author(
                    name=author_data.name,
                    affiliation=author_data.affiliation,
                    h_index=author_data.h_index,
                    semantic_scholar_id=author_data.semantic_scholar_id,
                )
                paper.authors.append(author)

            self.db.add(paper)
            await self.db.commit()
            await self.db.refresh(paper)

            return paper
        except Exception as e:
            print(f"[Fetch Error] Failed to create paper: {e}")
            import traceback
            traceback.print_exc()
            await self.db.rollback()
            raise
    
    async def _update_paper(self, paper: Paper, paper_data: PaperData):
        """Update existing paper with new data."""
        # Update fields that might have changed
        if paper_data.citations is not None:
            paper.citations = paper_data.citations
        if paper_data.influential_citations is not None:
            paper.influential_citations = paper_data.influential_citations
        if paper_data.altmetric_score is not None:
            paper.altmetric_score = paper_data.altmetric_score
        
        await self.db.commit()
    
    async def get_status(self, job_id: int) -> dict:
        """Get fetch job status."""
        result = await self.db.execute(select(FetchJob).where(FetchJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            return {"error": "Job not found"}
        
        return {
            "job_id": job.id,
            "status": job.status.value,
            "progress": job.progress,
            "current_source": job.current_source,
            "papers_fetched": job.papers_fetched,
            "papers_new": job.papers_new,
            "papers_updated": job.papers_updated,
            "errors": job.errors,
            "started_at": job.started_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }


async def execute_fetch_background(
    job_id: int,
    sources: List[str],
    keywords: Optional[List[str]],
    max_results: int,
    days_back: int,
):
    """Execute fetch in background with a dedicated session."""
    from app.core.database import async_session_maker
    
    async with async_session_maker() as session:
        service = FetchService(session)
        await service.run_fetch(
            job_id=job_id,
            sources=sources,
            keywords=keywords,
            max_results=max_results,
            days_back=days_back,
        )
