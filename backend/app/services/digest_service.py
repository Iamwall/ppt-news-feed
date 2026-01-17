"""Service for creating and processing digests."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.paper import Paper
from app.models.digest import Digest, DigestPaper, DigestStatus
from app.ai.summarizer import Summarizer
from app.ai.image_gen import ImageGenerator
from app.analysis.credibility import CredibilityAnalyzer


class DigestService:
    """Service for managing digest creation and processing."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_digest(
        self,
        name: str,
        paper_ids: List[int],
        ai_provider: str = "gemini",
        ai_model: str = "gemini-2.0-flash-exp",
        summary_style: str = "newsletter",
        generate_images: bool = True,
    ) -> Digest:
        """Create a new digest from selected papers."""
        
        digest = Digest(
            name=name,
            ai_provider=ai_provider,
            ai_model=ai_model,
            summary_style=summary_style,
            status=DigestStatus.PENDING,
        )
        self.db.add(digest)
        await self.db.commit()
        await self.db.refresh(digest)
        
        # Add papers to digest
        for i, paper_id in enumerate(paper_ids):
            digest_paper = DigestPaper(
                digest_id=digest.id,
                paper_id=paper_id,
                order=i,
            )
            self.db.add(digest_paper)
        
        await self.db.commit()
        await self.db.refresh(digest)
        
        return digest
    
    async def process_digest(self, digest_id: int):
        """Process a digest: analyze credibility, generate summaries and images."""
        from sqlalchemy.orm import selectinload

        # Get digest with papers eagerly loaded
        result = await self.db.execute(
            select(Digest)
            .options(selectinload(Digest.digest_papers))
            .where(Digest.id == digest_id)
        )
        digest = result.scalar_one_or_none()

        if not digest:
            return

        digest.status = DigestStatus.PROCESSING

        # Store digest_papers before commit to avoid lazy loading issues
        digest_papers_list = list(digest.digest_papers)
        paper_ids = [dp.paper_id for dp in digest_papers_list]

        await self.db.commit()

        try:
            print(f"[Digest] Initializing services for digest {digest_id}")
            # Initialize services
            summarizer = Summarizer(
                provider=digest.ai_provider,
                model=digest.ai_model,
            )
            image_gen = ImageGenerator()
            credibility = CredibilityAnalyzer(self.db)

            print(f"[Digest] Loading {len(paper_ids)} papers")
            # Get papers with authors eagerly loaded
            papers = []
            for paper_id in paper_ids:
                result = await self.db.execute(
                    select(Paper)
                    .options(selectinload(Paper.authors))
                    .where(Paper.id == paper_id)
                )
                paper = result.scalar_one_or_none()
                if paper:
                    papers.append(paper)
                    print(f"[Digest] Loaded paper {paper_id}: {paper.title[:50]}")

            print(f"[Digest] Processing {len(papers)} papers")
            # Process each paper
            for i, paper in enumerate(papers):
                print(f"[Digest] Processing paper {i+1}/{len(papers)}: {paper.title[:50]}")
                # Analyze credibility if not done
                if paper.credibility_score is None:
                    score, breakdown, note = await credibility.analyze(paper)
                    paper.credibility_score = score
                    paper.credibility_breakdown = breakdown
                    # Generate AI-powered credibility assessment
                    paper.credibility_note = await credibility.generate_ai_credibility_note(
                        paper, score, breakdown,
                        provider=digest.ai_provider,
                        model=digest.ai_model
                    )
                
                # Generate summary if not done
                if paper.summary_headline is None:
                    summary = await summarizer.summarize(
                        paper,
                        style=digest.summary_style,
                    )
                    paper.summary_headline = summary.headline
                    paper.summary_takeaway = summary.takeaway
                    paper.summary_why_matters = summary.why_matters
                    paper.key_takeaways = summary.key_takeaways
                    paper.tags = summary.tags
                
                # Generate image if not done
                if paper.image_path is None:
                    image_path = await image_gen.generate(paper)
                    paper.image_path = image_path
                
                await self.db.commit()
            
            # Generate intro, connecting narrative, and conclusion for digest
            print(f"[Digest] Generating interconnected narrative...")
            intro, narrative, conclusion = await summarizer.generate_digest_texts(
                papers,
                digest.name,
            )
            digest.intro_text = intro
            digest.connecting_narrative = narrative
            digest.conclusion_text = conclusion

            # Generate summary infographic for Final Thoughts section (Da Vinci style)
            print(f"[Digest] Generating summary infographic...")
            summary_image_path = await image_gen.generate_summary_infographic(
                papers,
                digest.name,
            )
            digest.summary_image_path = summary_image_path
            print(f"[Digest] Summary infographic saved: {summary_image_path}")

            digest.status = DigestStatus.COMPLETED
            digest.processed_at = datetime.utcnow()
            
        except Exception as e:
            digest.status = DigestStatus.FAILED
            digest.error_message = str(e)

        await self.db.commit()


async def execute_digest_background(digest_id: int):
    """Execute digest processing in background with a dedicated session."""
    import traceback
    from app.core.database import async_session_maker

    try:
        print(f"[Digest] Starting background processing for digest {digest_id}")
        async with async_session_maker() as session:
            service = DigestService(session)
            await service.process_digest(digest_id)
        print(f"[Digest] Completed processing digest {digest_id}")
    except Exception as e:
        print(f"[Digest Error] Failed to process digest {digest_id}: {e}")
        traceback.print_exc()
