"""PDF text extraction service for uploaded articles."""
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from PyPDF2 import PdfReader


@dataclass
class ExtractedPaper:
    """Extracted data from a PDF article."""
    title: str
    abstract: Optional[str]
    full_text: str
    authors: list[str]
    published_date: Optional[datetime]
    file_path: str


class PdfExtractor:
    """Extract text and metadata from PDF files."""
    
    def __init__(self):
        self.title_patterns = [
            # Common title patterns at start of document
            r'^([A-Z][^\n]{20,200})$',  # Capitalized line 20-200 chars
            r'^Title:\s*(.+)$',
            r'^(.{20,200})\n\n',  # First substantial line followed by blank
        ]
        
        self.abstract_patterns = [
            r'(?:Abstract|ABSTRACT)[:\s]*\n?(.*?)(?:\n\n|\nIntroduction|\nKeywords|\n1\.)',
            r'(?:Summary|SUMMARY)[:\s]*\n?(.*?)(?:\n\n|\nIntroduction)',
        ]
        
        self.author_patterns = [
            r'(?:Authors?|By)[:\s]*([^\n]+)',
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)*)',
        ]
    
    def extract(self, file_path: str | Path) -> ExtractedPaper:
        """Extract text and metadata from a PDF file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"Not a PDF file: {file_path}")
        
        reader = PdfReader(str(file_path))
        
        # Extract full text
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
        
        full_text = full_text.strip()
        
        if not full_text:
            raise ValueError("Could not extract any text from PDF")
        
        # Extract metadata
        title = self._extract_title(full_text, reader)
        abstract = self._extract_abstract(full_text)
        authors = self._extract_authors(full_text, reader)
        published_date = self._extract_date(reader)
        
        return ExtractedPaper(
            title=title,
            abstract=abstract,
            full_text=full_text,
            authors=authors,
            published_date=published_date,
            file_path=str(file_path),
        )
    
    def _extract_title(self, text: str, reader: PdfReader) -> str:
        """Extract title from PDF metadata or text."""
        # Try PDF metadata first
        if reader.metadata and reader.metadata.title:
            title = reader.metadata.title.strip()
            if len(title) > 10:  # Sanity check
                return title
        
        # Fall back to text extraction
        lines = text.split('\n')
        
        # Find first substantial non-empty line
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if len(line) >= 20 and len(line) <= 300:
                # Skip common header patterns
                if not re.match(r'^(Page|Vol\.|Issue|Journal|ISSN|DOI)', line, re.I):
                    return line
        
        # Last resort: first 100 chars
        return text[:100].split('\n')[0].strip() or "Untitled Document"
    
    def _extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from text."""
        for pattern in self.abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up and limit length
                abstract = re.sub(r'\s+', ' ', abstract)
                if len(abstract) > 50:
                    return abstract[:2000]
        
        # Fall back to first ~500 chars after title
        lines = text.split('\n')
        content_start = 0
        
        for i, line in enumerate(lines[:10]):
            if len(line.strip()) > 50:
                content_start = i + 1
                break
        
        remaining = '\n'.join(lines[content_start:content_start + 20])
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        
        if len(remaining) > 100:
            return remaining[:500]
        
        return None
    
    def _extract_authors(self, text: str, reader: PdfReader) -> list[str]:
        """Extract author names."""
        authors = []
        
        # Try PDF metadata
        if reader.metadata and reader.metadata.author:
            author_str = reader.metadata.author
            # Split by common delimiters
            for author in re.split(r'[,;]|and|\s+&\s+', author_str):
                author = author.strip()
                if author and len(author) > 2:
                    authors.append(author)
        
        if authors:
            return authors[:10]  # Limit to 10 authors
        
        # Try text patterns
        for pattern in self.author_patterns:
            match = re.search(pattern, text[:2000], re.MULTILINE)
            if match:
                author_str = match.group(1)
                for author in re.split(r'[,;]|and|\s+&\s+', author_str):
                    author = author.strip()
                    if author and len(author) > 2 and len(author) < 50:
                        authors.append(author)
                if authors:
                    return authors[:10]
        
        return []
    
    def _extract_date(self, reader: PdfReader) -> Optional[datetime]:
        """Extract publication date from PDF metadata."""
        if reader.metadata:
            # Try creation date
            if hasattr(reader.metadata, 'creation_date') and reader.metadata.creation_date:
                try:
                    return reader.metadata.creation_date
                except (ValueError, TypeError):
                    pass
            
            # Try modification date
            if hasattr(reader.metadata, 'modification_date') and reader.metadata.modification_date:
                try:
                    return reader.metadata.modification_date
                except (ValueError, TypeError):
                    pass
        
        return None


# Singleton instance
pdf_extractor = PdfExtractor()
