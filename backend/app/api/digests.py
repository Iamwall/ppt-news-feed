"""Digest-related API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.digest import Digest, DigestPaper, DigestStatus
from app.models.paper import Paper
from app.models.schemas import DigestCreateRequest
from app.api.papers import paper_to_dict

router = APIRouter()


def digest_to_dict(digest: Digest, include_papers: bool = True) -> dict:
    """Convert Digest model to dict."""
    result = {
        "id": digest.id,
        "name": digest.name,
        "status": digest.status.value if digest.status else "pending",
        "error_message": digest.error_message,
        "ai_provider": digest.ai_provider,
        "ai_model": digest.ai_model,
        "summary_style": digest.summary_style,
        "intro_text": digest.intro_text,
        "connecting_narrative": digest.connecting_narrative,
        "conclusion_text": digest.conclusion_text,
        "summary_image_path": digest.summary_image_path,
        "created_at": digest.created_at.isoformat() if digest.created_at else None,
        "processed_at": digest.processed_at.isoformat() if digest.processed_at else None,
    }
    
    if include_papers and hasattr(digest, 'digest_papers'):
        result["digest_papers"] = [
            {
                "order": dp.order,
                "paper": paper_to_dict(dp.paper) if dp.paper else None
            }
            for dp in digest.digest_papers
        ]
    else:
        result["digest_papers"] = []
    
    return result


@router.get("/")
async def list_digests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all digests with pagination."""
    query = select(Digest).options(
        selectinload(Digest.digest_papers).selectinload(DigestPaper.paper).selectinload(Paper.authors)
    ).order_by(desc(Digest.created_at))
    
    if status:
        query = query.where(Digest.status == status)
    
    # Get total
    count_result = await db.execute(select(func.count(Digest.id)))
    total = count_result.scalar() or 0
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    digests = result.scalars().all()
    
    return {
        "digests": [digest_to_dict(d) for d in digests],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/")
async def create_digest(
    request: DigestCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new digest from selected papers."""
    from app.services.digest_service import DigestService, execute_digest_background

    service = DigestService(db)
    digest = await service.create_digest(
        name=request.name,
        paper_ids=request.paper_ids,
        ai_provider=request.ai_provider,
        ai_model=request.ai_model,
        summary_style=request.summary_style.value if hasattr(request.summary_style, 'value') else request.summary_style,
        generate_images=request.generate_images,
    )

    # Process digest in background
    background_tasks.add_task(execute_digest_background, digest.id)

    return digest_to_dict(digest, include_papers=False)


@router.get("/{digest_id}")
async def get_digest(digest_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific digest."""
    result = await db.execute(
        select(Digest).options(
            selectinload(Digest.digest_papers).selectinload(DigestPaper.paper).selectinload(Paper.authors)
        ).where(Digest.id == digest_id)
    )
    digest = result.scalar_one_or_none()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    return digest_to_dict(digest)


@router.post("/{digest_id}/regenerate")
async def regenerate_digest(
    digest_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate summaries for a digest."""
    from app.services.digest_service import DigestService, execute_digest_background

    result = await db.execute(select(Digest).where(Digest.id == digest_id))
    digest = result.scalar_one_or_none()

    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")

    digest.status = DigestStatus.PROCESSING
    await db.commit()

    background_tasks.add_task(execute_digest_background, digest_id)

    return {"message": "Digest regeneration started"}


@router.delete("/{digest_id}")
async def delete_digest(digest_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a digest."""
    result = await db.execute(select(Digest).where(Digest.id == digest_id))
    digest = result.scalar_one_or_none()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    await db.delete(digest)
    return {"message": "Digest deleted successfully"}
