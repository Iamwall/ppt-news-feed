"""Full E2E Test: Applied Positive Psychology Digest"""
import asyncio
import sys
sys.path.insert(0, ".")

async def run_positive_psychology_test():
    print("=" * 70)
    print("E2E TEST: APPLIED POSITIVE PSYCHOLOGY DIGEST")
    print("=" * 70)
    
    from app.core.database import async_session_maker, init_db
    from app.core.config import settings
    
    # Check configuration
    print(f"\n[CONFIG] DEMO_MODE: {settings.demo_mode}")
    print(f"[CONFIG] AI Provider: {settings.default_ai_provider}")
    print(f"[CONFIG] Image Provider: {settings.default_image_provider}")
    print(f"[CONFIG] GROQ_API_KEY: {'SET' if settings.groq_api_key else 'NOT SET'}")
    print(f"[CONFIG] GOOGLE_API_KEY: {'SET' if settings.google_api_key else 'NOT SET'}")
    
    await init_db()
    
    # Step 1: Fetch papers on positive psychology
    print("\n" + "=" * 70)
    print("STEP 1: FETCHING PAPERS ON 'APPLIED POSITIVE PSYCHOLOGY'")
    print("=" * 70)
    
    from app.fetchers import get_fetcher
    
    fetcher = get_fetcher("pubmed")
    papers_data = []
    keywords = ["applied positive psychology", "wellbeing interventions"]
    
    print(f"Searching with keywords: {keywords}")
    async for paper in fetcher.fetch(keywords=keywords, max_results=4, days_back=60):
        papers_data.append(paper)
        print(f"  ✓ Found: {paper.title[:60]}...")
    
    if len(papers_data) < 3:
        # Try broader search
        print("  Broadening search with 'positive psychology'...")
        async for paper in fetcher.fetch(keywords=["positive psychology"], max_results=4, days_back=60):
            if len(papers_data) < 4:
                papers_data.append(paper)
                print(f"  ✓ Found: {paper.title[:60]}...")
    
    print(f"\nTotal papers found: {len(papers_data)}")
    
    if not papers_data:
        print("ERROR: No papers found!")
        return
    
    # Step 2: Save to database
    print("\n" + "=" * 70)
    print("STEP 2: SAVING PAPERS TO DATABASE")
    print("=" * 70)
    
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
                is_peer_reviewed=pd.is_peer_reviewed,
            )
            for author in pd.authors[:5]:
                paper.authors.append(Author(name=author.name, affiliation=author.affiliation))
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
            paper_ids.append(paper.id)
            print(f"  ✓ Saved paper ID {paper.id}")
    
    # Step 3: Create Digest
    print("\n" + "=" * 70)
    print("STEP 3: CREATING DIGEST")
    print("=" * 70)
    
    from app.models.digest import Digest, DigestPaper, DigestStatus
    
    async with async_session_maker() as session:
        digest = Digest(
            name="Applied Positive Psychology Digest",
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
        
        digest_id = digest.id
        print(f"  ✓ Created digest ID: {digest_id}")
    
    # Step 4: Process Digest (AI summarization, credibility, images)
    print("\n" + "=" * 70)
    print("STEP 4: PROCESSING DIGEST WITH AI")
    print("(This will take 1-2 minutes for summarization + image generation)")
    print("=" * 70)
    
    from app.services.digest_service import DigestService
    
    async with async_session_maker() as session:
        service = DigestService(session)
        await service.process_digest(digest_id)
    
    # Step 5: Display Results
    print("\n" + "=" * 70)
    print("STEP 5: RESULTS")
    print("=" * 70)
    
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Digest)
            .options(selectinload(Digest.digest_papers).selectinload(DigestPaper.paper))
            .where(Digest.id == digest_id)
        )
        digest = result.scalar_one()
        
        print(f"\nDigest: {digest.name}")
        print(f"Status: {digest.status.value}")
        
        if digest.status == DigestStatus.FAILED:
            print(f"ERROR: {digest.error_message}")
            return
        
        print("\n--- INTRODUCTION ---")
        print(digest.intro_text[:300] if digest.intro_text else "MISSING")
        
        print("\n--- CONNECTING NARRATIVE ---")
        print(digest.connecting_narrative[:300] if digest.connecting_narrative else "MISSING")
        
        print("\n--- PAPERS ---")
        for i, dp in enumerate(digest.digest_papers):
            paper = dp.paper
            print(f"\n[PAPER {i+1}]")
            print(f"  Title: {paper.title[:70]}...")
            print(f"  Headline: {paper.summary_headline or 'MISSING'}")
            print(f"  Takeaway: {(paper.summary_takeaway or 'MISSING')[:100]}...")
            print(f"  Key Takeaways: {len(paper.key_takeaways or [])} items")
            print(f"  Credibility: {paper.credibility_score}/100")
            print(f"  AI Analysis: {(paper.credibility_note or 'MISSING')[:100]}...")
            print(f"  Image: {paper.image_path or 'NOT GENERATED'}")
        
        print("\n--- CONCLUSION ---")
        print(digest.conclusion_text[:300] if digest.conclusion_text else "MISSING")
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        all_pass = all([
            digest.intro_text,
            digest.connecting_narrative,
            digest.conclusion_text,
            all(dp.paper.summary_headline for dp in digest.digest_papers),
            all(dp.paper.credibility_score for dp in digest.digest_papers),
        ])
        
        print(f"✓ Intro: {'YES' if digest.intro_text else 'NO'}")
        print(f"✓ Narrative: {'YES' if digest.connecting_narrative else 'NO'}")
        print(f"✓ Conclusion: {'YES' if digest.conclusion_text else 'NO'}")
        print(f"✓ All Headlines: {'YES' if all(dp.paper.summary_headline for dp in digest.digest_papers) else 'NO'}")
        print(f"✓ All Credibility: {'YES' if all(dp.paper.credibility_score for dp in digest.digest_papers) else 'NO'}")
        print(f"✓ Images: {sum(1 for dp in digest.digest_papers if dp.paper.image_path)} / {len(digest.digest_papers)}")
        
        print(f"\n{'🎉 TEST PASSED!' if all_pass else '❌ TEST INCOMPLETE - Check logs'}")
        print(f"\nView digest at: http://localhost:5173/digests/{digest_id}")

if __name__ == "__main__":
    asyncio.run(run_positive_psychology_test())
