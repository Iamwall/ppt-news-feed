"""Debug digest processing to find exact error location."""
import asyncio
import sys

async def test_digest_processing():
    """Test digest processing with detailed error tracking."""
    from app.services.digest_service import DigestService
    from app.core.database import async_session_maker
    from sqlalchemy import select
    from app.models.digest import Digest

    digest_id = 11

    print(f"Testing digest {digest_id} processing...")

    try:
        async with async_session_maker() as session:
            print("[1] Created session")

            service = DigestService(session)
            print("[2] Created service")

            # Test the process_digest method
            await service.process_digest(digest_id)
            print("[3] Processing completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Failed at step: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_digest_processing())
