import asyncio
import io
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(os.getcwd())

from app.composers.pdf_composer import PDFComposer
from app.models.digest import Digest, DigestPaper
from app.models.paper import Paper, Author

async def test_pdf():
    # Mock data
    paper = Paper(
        id=1,
        title="Test Paper",
        url="https://example.com",
        summary_headline="A very important summary",
        summary_takeaway="People should read this.",
        summary_why_matters="It changes everything.",
        credibility_score=85,
        authors=[Author(name="John Doe")],
        published_date="2024-01-01"
    )
    
    digest = Digest(
        id=1,
        name="Test Digest",
        intro_text="Welcome to the test.",
        conclusion_text="Goodbye.",
        digest_papers=[DigestPaper(paper=paper)]
    )
    
    composer = PDFComposer()
    print("Generating PDF...")
    try:
        pdf_bytes = await composer.compose(digest)
        print(f"Success! PDF size: {len(pdf_bytes)} bytes")
        
        output_path = "test_output.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved to {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pdf())
