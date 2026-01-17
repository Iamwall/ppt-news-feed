"""Paper-related API endpoints."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.paper import Paper, Author
from app.services.pdf_extractor import pdf_extractor

router = APIRouter()


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF article and extract its content."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.content_type and file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Invalid content type, expected application/pdf")
    
    # Create upload directory if needed
    upload_dir = Path(settings.upload_dir) / "pdfs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file with unique name
    file_id = uuid.uuid4().hex[:12]
    safe_filename = f"{file_id}_{file.filename.replace(' ', '_')}"
    file_path = upload_dir / safe_filename
    
    try:
        # Save uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text and metadata
        extracted = pdf_extractor.extract(file_path)
        
        # Create Paper record
        paper = Paper(
            title=extracted.title,
            abstract=extracted.abstract,
            source="upload",
            source_id=file_id,
            url=f"/uploads/pdfs/{safe_filename}",
            published_date=extracted.published_date,
            fetched_at=datetime.utcnow(),
            is_preprint=False,
            is_peer_reviewed=False,  # Unknown for uploads
        )
        
        # Add authors
        for author_name in extracted.authors[:10]:
            author = Author(name=author_name)
            paper.authors.append(author)
        
        db.add(paper)
        await db.commit()
        await db.refresh(paper)
        
        return {
            "message": "PDF uploaded and processed successfully",
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract[:200] + "..." if paper.abstract and len(paper.abstract) > 200 else paper.abstract,
                "authors": [a.name for a in paper.authors],
                "source": paper.source,
            }
        }
        
    except ValueError as e:
        # Clean up file on extraction error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Clean up file on any error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


def paper_to_dict(paper: Paper) -> dict:
    """Convert Paper model to dict for JSON response."""
    return {
        "id": paper.id,
        "title": paper.title,
        "abstract": paper.abstract,
        "journal": paper.journal,
        "doi": paper.doi,
        "url": paper.url,
        "source": paper.source,
        "source_id": paper.source_id,
        "published_date": paper.published_date.isoformat() if paper.published_date else None,
        "fetched_at": paper.fetched_at.isoformat() if paper.fetched_at else None,
        "citations": paper.citations,
        "influential_citations": paper.influential_citations,
        "altmetric_score": paper.altmetric_score,
        "credibility_score": paper.credibility_score,
        "credibility_breakdown": paper.credibility_breakdown,
        "summary_headline": paper.summary_headline,
        "summary_takeaway": paper.summary_takeaway,
        "summary_why_matters": paper.summary_why_matters,
        "key_takeaways": paper.key_takeaways,
        "credibility_note": paper.credibility_note,
        "tags": paper.tags,
        "image_path": paper.image_path,
        "study_type": paper.study_type,
        "sample_size": paper.sample_size,
        "methodology_quality": paper.methodology_quality,
        "is_preprint": paper.is_preprint,
        "authors": [{"id": a.id, "name": a.name, "affiliation": a.affiliation, "h_index": a.h_index} for a in paper.authors],
    }


@router.get("/")
async def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    source: Optional[str] = None,
    min_credibility: Optional[float] = Query(None, ge=0, le=100),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """List papers with optional filtering."""
    query = select(Paper).options(selectinload(Paper.authors)).order_by(desc(Paper.fetched_at))
    
    if source:
        query = query.where(Paper.source == source)
    if min_credibility is not None:
        query = query.where(Paper.credibility_score >= min_credibility)
    if from_date:
        query = query.where(Paper.published_date >= from_date)
    if to_date:
        query = query.where(Paper.published_date <= to_date)
    
    # Get total count
    count_result = await db.execute(select(func.count(Paper.id)))
    total = count_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    papers = result.scalars().all()
    
    return {
        "papers": [paper_to_dict(p) for p in papers],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{paper_id}")
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific paper by ID."""
    result = await db.execute(
        select(Paper).options(selectinload(Paper.authors)).where(Paper.id == paper_id)
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return paper_to_dict(paper)


@router.delete("/{paper_id}")
async def delete_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a paper."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    await db.delete(paper)
    await db.commit()
    return {"message": "Paper deleted successfully"}


@router.post("/reset-summaries")
async def reset_paper_summaries(db: AsyncSession = Depends(get_db)):
    """Reset all paper summaries so they can be regenerated with current AI settings."""
    result = await db.execute(select(Paper))
    papers = result.scalars().all()

    reset_count = 0
    for paper in papers:
        # Reset ALL papers that have any summary data (including demo/fallback data)
        if paper.summary_headline is not None:
            paper.summary_headline = None
            paper.summary_takeaway = None
            paper.summary_why_matters = None
            paper.key_takeaways = None
            paper.credibility_note = None
            paper.credibility_score = None
            paper.credibility_breakdown = None
            paper.tags = None
            reset_count += 1

    await db.commit()
    return {"message": f"Reset summaries for {reset_count} papers. Create a new digest to regenerate with Gemini AI."}


@router.post("/reset-images")
async def reset_paper_images(db: AsyncSession = Depends(get_db)):
    """Reset all paper images so they can be regenerated with new style settings."""
    result = await db.execute(select(Paper).where(Paper.image_path.isnot(None)))
    papers = result.scalars().all()

    reset_count = 0
    for paper in papers:
        paper.image_path = None
        reset_count += 1

    await db.commit()
    return {"message": f"Reset images for {reset_count} papers. Create a new digest to regenerate images with the new style."}
