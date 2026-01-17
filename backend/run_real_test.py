"""Test script to fetch real papers and generate a digest."""
import os
import asyncio
import sys

# Set environment variables FIRST before importing anything else
# NOTE: API keys should be set in .env or as environment variables before running
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./science_digest.db"
os.environ["DEBUG"] = "True"
# GROQ_API_KEY and GOOGLE_API_KEY must be set in environment or .env file
os.environ["DEFAULT_AI_PROVIDER"] = "groq"
os.environ["DEFAULT_AI_MODEL"] = "llama-3.3-70b-versatile"

from datetime import datetime
from app.core.database import init_db, async_session_maker
from app.fetchers.arxiv import ArxivFetcher
from app.models.paper import Paper, Author
from app.analysis.credibility import CredibilityAnalyzer
from app.ai.summarizer import Summarizer
from app.ai.providers.base import get_ai_provider
from app.core.config import settings


async def fetch_real_papers(keywords: list[str], max_results: int = 10):
    """Fetch real papers from arXiv."""
    print(f"\n[FETCH] Fetching {max_results} papers from arXiv...")
    print(f"[FETCH] Keywords: {', '.join(keywords)}")
    
    fetcher = ArxivFetcher()
    papers_data = []
    
    async for paper_data in fetcher.fetch(
        keywords=keywords,
        max_results=max_results,
        days_back=14,
    ):
        papers_data.append(paper_data)
        print(f"  - Found: {paper_data.title[:60]}...")
    
    print(f"[FETCH] Retrieved {len(papers_data)} papers")
    return papers_data


async def save_papers_to_db(papers_data, db):
    """Save papers to database."""
    print(f"\n[DB] Saving {len(papers_data)} papers to database...")
    
    saved_papers = []
    for paper_data in papers_data:
        paper = Paper(
            title=paper_data.title,
            abstract=paper_data.abstract,
            journal=paper_data.journal,
            doi=paper_data.doi,
            url=paper_data.url,
            source=paper_data.source,
            source_id=paper_data.source_id,
            published_date=paper_data.published_date,
            is_preprint=paper_data.is_preprint,
            fetched_at=datetime.utcnow(),
        )
        
        # Add authors
        for author_data in paper_data.authors[:5]:  # Limit to first 5 authors
            author = Author(
                name=author_data.name,
                affiliation=author_data.affiliation,
            )
            paper.authors.append(author)
        
        db.add(paper)
        saved_papers.append(paper)
    
    await db.commit()
    
    # Refresh to get IDs
    for paper in saved_papers:
        await db.refresh(paper)
    
    print(f"[DB] Saved {len(saved_papers)} papers")
    return saved_papers


async def analyze_credibility(papers, db):
    """Run credibility analysis on papers."""
    print(f"\n[CREDIBILITY] Analyzing {len(papers)} papers...")
    
    analyzer = CredibilityAnalyzer(db)
    
    for paper in papers:
        score, breakdown, note = await analyzer.analyze(paper)
        paper.credibility_score = score
        paper.credibility_breakdown = breakdown
        paper.credibility_note = note
        print(f"  - {paper.title[:50]}... Score: {score:.1f}/100")
    
    await db.commit()
    print("[CREDIBILITY] Analysis complete")


async def generate_summaries(papers, db):
    """Generate AI summaries for papers."""
    print(f"\n[AI] Generating summaries using Groq (llama-3.3-70b-versatile)...")
    
    summarizer = Summarizer(provider="groq", model="llama-3.3-70b-versatile")
    
    for i, paper in enumerate(papers):
        print(f"  [{i+1}/{len(papers)}] Summarizing: {paper.title[:50]}...")
        
        try:
            result = await summarizer.summarize(paper)
            
            # PaperSummary is a dataclass, access attributes directly
            paper.summary_headline = result.headline
            paper.summary_takeaway = result.takeaway
            paper.summary_why_matters = result.why_matters
            paper.tags = result.tags
            
            headline_preview = paper.summary_headline[:60] if paper.summary_headline else "No headline"
            print(f"      Headline: {headline_preview}...")
            
        except Exception as e:
            print(f"      Error: {e}")
            import traceback
            traceback.print_exc()
            paper.summary_headline = f"Error generating summary: {str(e)}"
    
    await db.commit()
    print("[AI] Summaries complete")


async def create_newsletter_preview(papers):
    """Create a simple newsletter preview."""
    print("\n" + "="*80)
    print("                    SCIENCE DIGEST NEWSLETTER")
    print("                    " + datetime.now().strftime("%B %d, %Y"))
    print("="*80)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{'─'*80}")
        print(f"[{i}] {paper.summary_headline or paper.title}")
        print(f"{'─'*80}")
        
        if paper.summary_takeaway:
            print(f"\nKEY TAKEAWAY: {paper.summary_takeaway}")
        
        if paper.summary_why_matters:
            print(f"\nWHY IT MATTERS: {paper.summary_why_matters}")
        
        print(f"\nSOURCE: {paper.journal}")
        print(f"CREDIBILITY: {paper.credibility_score:.0f}/100" if paper.credibility_score else "")
        
        if paper.tags:
            print(f"TAGS: {', '.join(paper.tags)}")
        
        print(f"LINK: {paper.url}")
    
    print("\n" + "="*80)
    print("                    END OF NEWSLETTER")
    print("="*80)


async def main():
    print("="*60)
    print("  SCIENCE DIGEST - REAL DATA TEST")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  - AI Provider: Groq (llama-3.3-70b-versatile)")
    print(f"  - Image Provider: Gemini")
    print(f"  - Database: SQLite (local)")
    
    # Initialize database
    print("\n[INIT] Initializing database...")
    await init_db()
    print("[INIT] Database ready")
    
    # Create session
    async with async_session_maker() as db:
        # Fetch real papers from arXiv
        keywords = ["artificial intelligence", "machine learning"]
        papers_data = await fetch_real_papers(keywords, max_results=5)
        
        if not papers_data:
            print("\n[ERROR] No papers fetched. Check your internet connection.")
            return
        
        # Save to database
        papers = await save_papers_to_db(papers_data, db)
        
        # Analyze credibility
        await analyze_credibility(papers, db)
        
        # Generate AI summaries
        await generate_summaries(papers, db)
        
        # Create newsletter preview
        await create_newsletter_preview(papers)
    
    print("\n[SUCCESS] Test complete! The application is working with real data.")
    print("\nNext steps:")
    print("  1. Start the web server: python run_demo.py")
    print("  2. Open http://localhost:8000/docs for API documentation")
    print("  3. View papers at http://localhost:8000/api/v1/papers/")


if __name__ == "__main__":
    asyncio.run(main())
