"""Test script to verify paper fetching works end-to-end."""
import asyncio
import sys
from sqlalchemy import select

from app.core.database import async_session_maker, init_db
from app.services.fetch_service import FetchService
from app.models.paper import Paper


async def main():
    """Test the fetch service."""
    print("Initializing database...")
    await init_db()

    print("\nTesting fetch service...")
    async with async_session_maker() as session:
        service = FetchService(session)

        # Create fetch job
        print("Creating fetch job...")
        job = await service.start_fetch(
            sources=["arxiv"],
            keywords=["quantum computing"],
            max_results=5,
            days_back=30,
        )
        print(f"Created job #{job.id}")

        # Run fetch
        print("\nFetching papers...")
        await service.run_fetch(
            job_id=job.id,
            sources=["arxiv"],
            keywords=["quantum computing"],
            max_results=5,
            days_back=30,
        )

        # Check results
        print("\nFetch completed! Checking results...")
        status = await service.get_status(job.id)
        print(f"Status: {status['status']}")
        print(f"Papers fetched: {status['papers_fetched']}")
        print(f"Papers new: {status['papers_new']}")
        print(f"Papers updated: {status['papers_updated']}")

        if status.get('errors'):
            print(f"Errors: {status['errors']}")

        # List papers in database
        print("\nPapers in database:")
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(Paper).options(selectinload(Paper.authors)).limit(5)
        )
        papers = result.scalars().all()

        for i, paper in enumerate(papers, 1):
            print(f"{i}. [{paper.source}] {paper.title[:60]}...")
            author_names = [a.name for a in paper.authors[:3]]
            if author_names:
                print(f"   Authors: {', '.join(author_names)}")
            print(f"   Published: {paper.published_date}")
            print()

        if not papers:
            print("No papers found in database!")
            return 1

        print(f"\n✓ Successfully fetched and stored {len(papers)} papers!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
