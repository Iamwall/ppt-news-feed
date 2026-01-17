
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, delete

# Add backend to path
# Add current directory to path
sys.path.append(os.getcwd())

from app.core.database import async_session_maker
from app.models.custom_source import CustomSource
from app.models.paper import Paper
from app.services.fetch_service import FetchService, PaperData
from app.services.live_pulse_service import LivePulseService

async def test_validation_logic():
    async with async_session_maker() as session:
        print("1. Creating test source...")
        source_id = "test_source_validation"
        
        # Clean up existing
        await session.execute(delete(CustomSource).where(CustomSource.source_id == source_id))
        await session.execute(delete(Paper).where(Paper.source_id == source_id))
        await session.commit()
        
        # Create unvalidated source
        source = CustomSource(
            domain_id="science",
            name="Test Validation Source",
            source_id=source_id, 
            source_type="rss",
            url="http://example.com/feed",
            is_validated=False
        )
        session.add(source)
        await session.commit()
        
        print("2. Fetching paper from unvalidated source...")
        fetch_service = FetchService(session)
        # Mock paper data
        paper_data = PaperData(
            title="Test Paper 1",
            abstract="Test Abstract 1",
            source="custom",
            source_id=source_id,
            url="http://example.com/1",
            published_date=datetime.now(),
            authors=[]
        )
        
        paper1 = await fetch_service._create_paper(paper_data)
        print(f"Paper 1 validated: {paper1.is_validated_source}")
        assert not paper1.is_validated_source, "Paper should not be validated yet"
        
        print("3. Validating source...")
        source.is_validated = True
        await session.commit()
        
        print("4. Fetching paper from validated source...")
        paper_data2 = PaperData(
            title="Test Paper 2",
            abstract="Test Abstract 2",
            source="custom",
            source_id=source_id,
            url="http://example.com/2",
            published_date=datetime.now(),
            authors=[]
        )
        
        paper2 = await fetch_service._create_paper(paper_data2)
        print(f"Paper 2 validated: {paper2.is_validated_source}")
        assert paper2.is_validated_source, "Paper should be validated now"
        
        print("5. Testing LivePulseService filter...")
        pulse_service = LivePulseService(session)
        
        # passed_triage_only defaults to True, so we must disable it since our mock papers aren't triaged
        feed = await pulse_service.get_feed(validated_only=True, passed_triage_only=False)
        print(f"Feed items count: {len(feed)}")
        
        found_paper2 = any(p.id == paper2.id for p in feed)
        
        print(f"Found Paper 2: {found_paper2}")
        
        assert found_paper2, "Should find validated paper"
        
        print("SUCCESS! All validation logic verified.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_validation_logic())
