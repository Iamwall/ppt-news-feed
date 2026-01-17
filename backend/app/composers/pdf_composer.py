"""PDF newsletter composer."""
import os
from pathlib import Path
import io
import uuid
from typing import Optional

from app.models.digest import Digest
from app.models.domain_config import DomainConfig
from app.core.config import settings


class PDFComposer:
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize with base URL for images."""
        self.base_url = base_url
    
    async def compose(self, digest: Digest, domain_config: Optional[DomainConfig] = None) -> bytes:
        """Generate PDF from digest and return bytes."""
        try:
            from xhtml2pdf import pisa
        except ImportError as e:
            raise Exception(f"xhtml2pdf not available: {e}")

        from app.composers.html_composer import HTMLComposer

        # Use same base_url for image resolution in HTML
        html_composer = HTMLComposer(base_url=self.base_url)
        html_content = await html_composer.compose(digest, for_preview=False, for_pdf=True, domain_config=domain_config)
        
        result = io.BytesIO()
        try:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=result,
                link_callback=self._fetch_resources
            )
            
            if pisa_status.err:
                raise Exception(f"PDF generation error code {pisa_status.err}")
                
            return result.getvalue()
        except Exception as e:
            raise Exception(f"PDF generation exception: {str(e)}")
    
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
            parts = uri.split('/')
            if 'images' in parts:
                local_path = Path(settings.generated_images_dir) / parts[-1]
                if local_path.exists():
                    return str(local_path)

        # Fallback to absolute URL if it starts with http
        if uri.startswith('http'):
            return uri
            
        return uri


