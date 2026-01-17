"""PDF newsletter composer."""
import os
from pathlib import Path
import uuid
from typing import Optional

from app.models.digest import Digest
from app.core.config import settings


class PDFComposer:
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize with base URL for images."""
        self.base_url = base_url
    
    async def compose(self, digest: Digest) -> str:
        """Generate PDF from digest."""
        try:
            from xhtml2pdf import pisa
        except ImportError as e:
            return self._create_error_file(digest, f"xhtml2pdf not available: {e}")
        
        from app.composers.html_composer import HTMLComposer
        
        # Use same base_url for image resolution in HTML
        html_composer = HTMLComposer(base_url=self.base_url)
        html_content = await html_composer.compose(digest, for_preview=False)
        
        # xhtml2pdf can be picky about some common modern CSS
        # Let's simplify some problematic ones if needed
        html_content = html_content.replace('width: 100%', 'width: 600px')
        
        filename = f"newsletter_{digest.id}_{uuid.uuid4().hex[:8]}.pdf"
        output_dir = Path(settings.upload_dir) / "pdfs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        try:
            with open(output_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf_file,
                    link_callback=self._fetch_resources
                )
            
            if pisa_status.err:
                return self._create_error_file(digest, f"PDF generation error code {pisa_status.err}")
                
            return str(output_path)
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            return self._create_error_file(digest, f"PDF generation exception: {str(e)}")
    
    def _fetch_resources(self, uri, rel):
        """Callback to handle images and other resources locally."""
        # Convert static URLs to local paths for xhtml2pdf
        if '/static/images/' in uri:
            filename = uri.split('/')[-1]
            local_path = Path(settings.generated_images_dir) / filename
            if local_path.exists():
                return str(local_path)
        
        # If it's a relative path starting with /static
        if uri.startswith('/static/'):
            # This shouldn't normally happen if we used absolute URLs in HTML
            parts = uri.split('/')
            if 'images' in parts:
                local_path = Path(settings.generated_images_dir) / parts[-1]
                if local_path.exists():
                    return str(local_path)

        # Fallback to absolute URL if it starts with http
        if uri.startswith('http'):
            return uri
            
        return uri


    def _create_error_file(self, digest: Digest, error_msg: str) -> str:
        """Create an error placeholder file."""
        output_dir = Path(settings.upload_dir) / "pdfs"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"error_{digest.id}_{uuid.uuid4().hex[:4]}.txt"
        path.write_text(f"Error: {error_msg}\nDigest: {digest.name}")
        return str(path)


