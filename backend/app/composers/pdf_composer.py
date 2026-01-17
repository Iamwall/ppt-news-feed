"""PDF newsletter composer."""
import os
from pathlib import Path
import uuid

# Try to import weasyprint - may not be available
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from app.models.digest import Digest
from app.core.config import settings


class PDFComposer:
    async def compose(self, digest: Digest) -> str:
        if not WEASYPRINT_AVAILABLE:
            return self._create_placeholder(digest)
        
        from app.composers.html_composer import HTMLComposer
        html_composer = HTMLComposer()
        html_content = await html_composer.compose(digest, for_email=False)
        
        pdf_css = CSS(string='@page { size: A4; margin: 1.5cm; }')
        filename = f"newsletter_{digest.id}_{uuid.uuid4().hex[:8]}.pdf"
        output_dir = Path(settings.upload_dir) / "pdfs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        html = HTML(string=html_content)
        html.write_pdf(output_path, stylesheets=[pdf_css])
        return str(output_path)
    
    def _create_placeholder(self, digest: Digest) -> str:
        output_dir = Path(settings.upload_dir) / "pdfs"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"placeholder_{digest.id}.txt"
        path.write_text(f"PDF generation requires weasyprint. Digest: {digest.name}")
        return str(path)
