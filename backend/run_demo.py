#!/usr/bin/env python
"""
Demo run script - Start the backend without external dependencies.

This script:
1. Creates the SQLite database
2. Seeds demo papers
3. Creates a demo digest
4. Starts the FastAPI server

Usage:
    python run_demo.py
"""
import asyncio
import uvicorn
from app.core.database import init_db, async_session_maker
from app.demo.mock_data import get_mock_papers, get_mock_summary, get_mock_credibility
from app.models.paper import Paper, Author
from app.models.digest import Digest, DigestPaper, DigestStatus
from datetime import datetime
from sqlalchemy import select


async def seed_demo_data():
    """Seed the database with demo data."""
    print("[*] Seeding demo data...")
    
    async with async_session_maker() as db:
        # Check if already seeded
        result = await db.execute(select(Paper).limit(1))
        if result.scalar_one_or_none():
            print("   Database already has data, skipping seed.")
            return
        
        # Seed papers
        mock_papers = get_mock_papers(8)
        papers = []
        
        for paper_data in mock_papers:
            summary = get_mock_summary(paper_data["title"])
            score, breakdown, note = get_mock_credibility(paper_data)
            
            paper = Paper(
                title=paper_data["title"],
                abstract=paper_data["abstract"],
                journal=paper_data["journal"],
                doi=paper_data.get("doi"),
                url=paper_data.get("url"),
                source=paper_data["source"],
                source_id=paper_data["source_id"],
                published_date=paper_data["published_date"],
                citations=paper_data.get("citations"),
                journal_impact_factor=paper_data.get("journal_impact_factor"),
                is_preprint=paper_data.get("is_preprint", False),
                is_peer_reviewed=not paper_data.get("is_preprint", False),
                summary_headline=summary["headline"],
                summary_takeaway=summary["takeaway"],
                summary_why_matters=summary["why_matters"],
                tags=summary["tags"],
                credibility_score=score,
                credibility_breakdown=breakdown,
                credibility_note=note,
            )
            
            for author_name in paper_data.get("authors", []):
                author = Author(
                    name=author_name,
                    h_index=50 + hash(author_name) % 30,
                )
                paper.authors.append(author)
            
            db.add(paper)
            papers.append(paper)
        
        await db.commit()
        
        # Refresh to get IDs
        for paper in papers:
            await db.refresh(paper)
        
        print(f"   Created {len(papers)} demo papers")
        
        # Create demo digest
        digest = Digest(
            name="Weekly Science Digest - Demo Edition",
            status=DigestStatus.COMPLETED,
            ai_provider="demo",
            ai_model="mock-v1",
            summary_style="newsletter",
            intro_text="Welcome to this week's science digest! We've curated the most impactful research from across scientific disciplines—from quantum computing breakthroughs to climate change insights. Each summary includes our credibility assessment to help you evaluate the findings.",
            conclusion_text="Thank you for reading this week's digest. Science advances one discovery at a time, and we're excited to bring you the latest. Stay curious, and see you next week!",
            processed_at=datetime.utcnow(),
        )
        db.add(digest)
        await db.commit()
        await db.refresh(digest)
        
        # Add papers to digest
        for i, paper in enumerate(papers):
            dp = DigestPaper(
                digest_id=digest.id,
                paper_id=paper.id,
                order=i,
            )
            db.add(dp)
        
        await db.commit()
        print(f"   Created demo digest (ID: {digest.id})")


async def main():
    """Initialize and run the demo."""
    print("\n=== Science Digest - Demo Mode ===")
    print("=" * 40)
    
    # Initialize database
    print("\n[*] Initializing database...")
    await init_db()
    print("    Database ready (SQLite)")
    
    # Seed demo data
    await seed_demo_data()
    
    print("\n[OK] Demo ready!")
    print("\n[*] Starting server...")
    print("    API:     http://localhost:8000")
    print("    Docs:    http://localhost:8000/docs")
    print("    Papers:  http://localhost:8000/api/v1/papers/")
    print("    Digests: http://localhost:8000/api/v1/digests/")
    print("\n    Press Ctrl+C to stop\n")


if __name__ == "__main__":
    # Run setup
    asyncio.run(main())
    
    # Start server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
