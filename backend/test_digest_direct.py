"""Test digest processing directly without background tasks."""
import asyncio

async def test_direct():
    from app.services.digest_service import execute_digest_background

    # Test with digest ID 6
    digest_id = 6
    print(f"Testing direct execution of digest {digest_id}...")

    await execute_digest_background(digest_id)

    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_direct())
