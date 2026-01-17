"""End-to-End System Test - Real Data Verification"""
import asyncio
import sys
sys.path.insert(0, ".")

async def run_e2e_test():
    print("=" * 60)
    print("END-TO-END SYSTEM VERIFICATION")
    print("=" * 60)
    
    from app.core.database import async_session_maker, init_db
    from app.core.config import settings
    
    # Step 0: Check configuration
    print("\n[STEP 0] Checking configuration...")
    print(f"  DEMO_MODE: {settings.demo_mode}")
    print(f"  GROQ_API_KEY: {'SET' if settings.groq_api_key else 'NOT SET'}")
    print(f"  GOOGLE_API_KEY: {'SET' if settings.google_api_key else 'NOT SET'}")
    print(f"  DEFAULT_AI_PROVIDER: {settings.default_ai_provider}")
    
    if settings.demo_mode:
        print("  [!] WARNING: Demo mode is ON. Real AI will not be used!")
    if not settings.groq_api_key:
        print("  [!] ERROR: Groq API key not set!")
        return
    
    # Initialize DB
    await init_db()
    
    # Step 1: Fetch papers
    print("\n[STEP 1] Fetching papers from PubMed...")
    from app.fetchers import get_fetcher
    
    fetcher = get_fetcher("pubmed")
    papers_data = []
    async for paper in fetcher.fetch(keywords=["artificial intelligence", "health"], max_results=3, days_back=30):
        papers_data.append(paper)
        print(f"  ✓ Fetched: {paper.title[:50]}...")
    
    if not papers_data:
        print("  [!] No papers fetched!")
        return
    
    # Step 2: Save papers to DB
    print("\n[STEP 2] Saving papers to database...")
    from app.models.paper import Paper, Author
    
    paper_ids = []
    async with async_session_maker() as session:
        for pd in papers_data:
            paper = Paper(
                title=pd.title,
                abstract=pd.abstract,
                journal=pd.journal,
                doi=pd.doi,
                url=pd.url,
                source=pd.source,
                source_id=pd.source_id,
                published_date=pd.published_date,
                is_preprint=pd.is_preprint,
            )
            for author_data in pd.authors[:5]:
                author = Author(name=author_data.name, affiliation=author_data.affiliation)
                paper.authors.append(author)
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
            paper_ids.append(paper.id)
            print(f"  ✓ Saved paper ID: {paper.id}")
    
    # Step 3: Create Digest
    print("\n[STEP 3] Creating digest...")
    from app.models.digest import Digest, DigestPaper, DigestStatus
    from datetime import datetime
    
    async with async_session_maker() as session:
        digest = Digest(
            name="E2E Test Digest",
            ai_provider="groq",
            ai_model="llama-3.3-70b-versatile",
            summary_style="newsletter",
            status=DigestStatus.PENDING,
        )
        session.add(digest)
        await session.commit()
        await session.refresh(digest)
        
        for i, paper_id in enumerate(paper_ids):
            dp = DigestPaper(digest_id=digest.id, paper_id=paper_id, order=i)
            session.add(dp)
        await session.commit()
        
        print(f"  ✓ Created digest ID: {digest.id}")
        digest_id = digest.id
    
    # Step 4: Process Digest (this calls the AI)
    print("\n[STEP 4] Processing digest with Groq AI...")
    print("  (This may take 30-60 seconds)")
    from app.services.digest_service import DigestService
    
    async with async_session_maker() as session:
        service = DigestService(session)
        await service.process_digest(digest_id)
    
    # Step 5: Verify Results
    print("\n[STEP 5] Verifying results...")
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Digest)
            .options(selectinload(Digest.digest_papers).selectinload(DigestPaper.paper))
            .where(Digest.id == digest_id)
        )
        digest = result.scalar_one()
        
        print(f"\n  Status: {digest.status.value}")
        
        if digest.status == DigestStatus.FAILED:
            print(f"  ERROR: {digest.error_message}")
            return
        
        print(f"\n  --- INTRO TEXT ---")
        print(f"  {digest.intro_text[:200] if digest.intro_text else 'MISSING'}...")
        
        print(f"\n  --- CONNECTING NARRATIVE ---")
        print(f"  {digest.connecting_narrative[:200] if digest.connecting_narrative else 'MISSING'}...")
        
        print(f"\n  --- CONCLUSION TEXT ---")
        print(f"  {digest.conclusion_text[:200] if digest.conclusion_text else 'MISSING'}...")
        
        # Check papers
        print(f"\n  --- PAPER SUMMARIES ---")
        for dp in digest.digest_papers:
            paper = dp.paper
            print(f"\n  Paper: {paper.title[:50]}...")
            print(f"    Headline: {paper.summary_headline or 'MISSING'}")
            print(f"    Takeaway: {(paper.summary_takeaway or 'MISSING')[:100]}...")
            print(f"    Key Takeaways: {paper.key_takeaways or 'MISSING'}")
            print(f"    Credibility: {paper.credibility_score}")
        
        # Verification
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS")
        print("=" * 60)
        
        checks = [
            ("Intro generated", bool(digest.intro_text and len(digest.intro_text) > 50)),
            ("Narrative generated", bool(digest.connecting_narrative and len(digest.connecting_narrative) > 50)),
            ("Conclusion generated", bool(digest.conclusion_text and len(digest.conclusion_text) > 50)),
            ("No 'demo' in intro", "demo" not in (digest.intro_text or "").lower()),
            ("Papers have headlines", all(dp.paper.summary_headline for dp in digest.digest_papers)),
            ("Papers have takeaways", all(dp.paper.summary_takeaway for dp in digest.digest_papers)),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {name}")
            if not passed:
                all_passed = False
        
        print("\n" + ("🎉 ALL CHECKS PASSED!" if all_passed else "❌ SOME CHECKS FAILED"))

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
