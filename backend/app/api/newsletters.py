"""Newsletter generation and export API endpoints."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.digest import Digest, DigestPaper
from app.models.paper import Paper
from app.models.schemas import NewsletterExportRequest, DigestStatus
from app.composers.html_composer import HTMLComposer
from app.composers.pdf_composer import PDFComposer
from app.composers.markdown_composer import MarkdownComposer

router = APIRouter()


def _get_digest_query(digest_id: int):
    """Get a query that eager-loads all related data for newsletter generation."""
    return select(Digest).options(
        selectinload(Digest.digest_papers)
        .selectinload(DigestPaper.paper)
        .selectinload(Paper.authors)
    ).where(Digest.id == digest_id)


@router.post("/{digest_id}/export")
async def export_newsletter(
    digest_id: int,
    request: NewsletterExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Export a digest as a newsletter in the specified format."""
    result = await db.execute(_get_digest_query(digest_id))
    digest = result.scalar_one_or_none()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    if digest.status != DigestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Digest is not yet complete")
    
    if request.format == "html":
        composer = HTMLComposer()
        content = await composer.compose(digest)
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=newsletter_{digest_id}.html"}
        )
    
    elif request.format == "pdf":
        composer = PDFComposer()
        pdf_path = await composer.compose(digest)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"newsletter_{digest_id}.pdf"
        )
    
    elif request.format == "markdown":
        composer = MarkdownComposer()
        content = await composer.compose(digest)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=newsletter_{digest_id}.md"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


@router.get("/{digest_id}/preview")
async def preview_newsletter(
    digest_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get HTML preview of the newsletter."""
    import traceback
    try:
        result = await db.execute(_get_digest_query(digest_id))
        digest = result.scalar_one_or_none()
        
        if not digest:
            raise HTTPException(status_code=404, detail="Digest not found")
        
        composer = HTMLComposer()
        content = await composer.compose(digest, for_preview=True)
        
        return Response(content=content, media_type="text/html")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{digest_id}/send")
async def send_newsletter(
    digest_id: int,
    recipients: list[str],
    db: AsyncSession = Depends(get_db),
):
    """Send the newsletter via email."""
    from app.services.email_service import EmailService
    
    result = await db.execute(_get_digest_query(digest_id))
    digest = result.scalar_one_or_none()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    if digest.status != DigestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Digest is not yet complete")
    
    composer = HTMLComposer()
    html_content = await composer.compose(digest, for_email=True)
    
    email_service = EmailService()
    results = await email_service.send_newsletter(
        recipients=recipients,
        subject=f"Science Digest: {digest.name}",
        html_content=html_content,
    )
    
    return {"sent": len([r for r in results if r["success"]]), "failed": len([r for r in results if not r["success"]])}

