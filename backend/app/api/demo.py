"""Demo mode API endpoints for testing without external APIs."""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.paper import Paper, Author
from app.models.digest import Digest, DigestPaper, DigestStatus
from app.demo.mock_data import get_mock_papers, get_mock_summary, get_mock_credibility

router = APIRouter()


@router.post("/seed-papers")
async def seed_demo_papers(db: AsyncSession = Depends(get_db)):
    """Seed the database with demo papers for testing."""
    mock_papers = get_mock_papers(8)
    created = 0
    
    for paper_data in mock_papers:
        # Check if already exists
        existing = await db.execute(
            select(Paper).where(Paper.source_id == paper_data["source_id"])
        )
        if existing.scalar_one_or_none():
            continue
        
        # Get mock summary and credibility
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
            # Pre-populated AI content
            summary_headline=summary["headline"],
            summary_takeaway=summary["takeaway"],
            summary_why_matters=summary["why_matters"],
            key_takeaways=summary.get("key_takeaways", []),
            tags=summary["tags"],
            credibility_score=score,
            credibility_breakdown=breakdown,
            credibility_note=note,
        )
        
        # Add authors
        for author_name in paper_data.get("authors", []):
            author = Author(
                name=author_name,
                h_index=50 + hash(author_name) % 30,  # Mock h-index
            )
            paper.authors.append(author)
        
        db.add(paper)
        created += 1
    
    await db.commit()
    
    return {
        "message": f"Seeded {created} demo papers",
        "total_papers": created,
    }


@router.post("/create-demo-digest")
async def create_demo_digest(db: AsyncSession = Depends(get_db)):
    """Create a demo digest with all seeded papers."""
    # Get all papers
    result = await db.execute(select(Paper).limit(8))
    papers = result.scalars().all()
    
    if not papers:
        return {"error": "No papers found. Run /seed-papers first."}
    
    # Create digest
    digest = Digest(
        name="Weekly Science Digest - Demo Edition",
        status=DigestStatus.COMPLETED,
        ai_provider="demo",
        ai_model="mock-v1",
        summary_style="newsletter",
        intro_text="Welcome to this week's science digest! We've curated the most impactful research from across scientific disciplines—from quantum computing breakthroughs to climate change insights. The thread connecting these diverse studies is human resilience: how we're adapting our biology, technology, and environment to meet future challenges.",
        connecting_narrative="<p>This week's research reveals a striking convergence between biological innovation and technological problem-solving. While the <strong>CRISPR</strong> and <strong>mRNA vaccine</strong> studies show us mastering our own biology to fight disease, the <strong>quantum computing</strong> and <strong>solar cell</strong> breakthroughs demonstrate our growing ability to manipulate physics for cleaner energy and faster computation.</p><p>Interestingly, the <strong>microplastics</strong> study serves as a sobering counter-narrative—a reminder that our technological progress often leaves biological footprints we must address. The <strong>climate change</strong> meta-analysis bridges these worlds, showing how biological systems are already adapting to our industrial impact. Together, these findings paint a picture of a world where the lines between natural evolution and human engineering are becoming increasingly blurred.</p>",
        conclusion_text="**The Big Picture**\n- We are entering an era of \"precision biology\" (CRISPR, mRNA).\n- AI is becoming a genuine partner in scientific discovery.\n- Climate adaptation is already happening at a global scale.\n\n**Living It**\nConsider how you interact with technology this week. Are there ways to use tools like AI to augment your own problem-solving, much like scientists are doing? Stay curious about the micro-impacts of your daily choices, from plastic use to energy consumption.",
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
    
    return {
        "message": "Demo digest created",
        "digest_id": digest.id,
        "papers_included": len(papers),
    }


@router.delete("/clear-all")
async def clear_demo_data(db: AsyncSession = Depends(get_db)):
    """Clear all demo data from the database."""
    from app.models.digest import DigestPaper, Digest
    from app.models.paper import Paper, Author
    from app.models.fetch_job import FetchJob
    
    # Delete in order due to foreign keys
    await db.execute(select(DigestPaper).where(True))
    for dp in (await db.execute(select(DigestPaper))).scalars().all():
        await db.delete(dp)
    
    for digest in (await db.execute(select(Digest))).scalars().all():
        await db.delete(digest)
    
    for author in (await db.execute(select(Author))).scalars().all():
        await db.delete(author)
    
    for paper in (await db.execute(select(Paper))).scalars().all():
        await db.delete(paper)
    
    for job in (await db.execute(select(FetchJob))).scalars().all():
        await db.delete(job)
    
    await db.commit()
    
    return {"message": "All data cleared"}
