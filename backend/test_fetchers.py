"""Test fetchers directly."""
import asyncio
import sys
sys.path.insert(0, ".")

async def test_fetchers():
    print("Testing fetchers directly...\n")
    
    from app.fetchers import get_fetcher
    
    sources = ["pubmed", "arxiv"]  # Start with known-working sources
    
    for source in sources:
        print(f"\n=== Testing {source} ===")
        try:
            fetcher = get_fetcher(source)
            count = 0
            async for paper in fetcher.fetch(keywords=["cancer"], max_results=3, days_back=30):
                count += 1
                print(f"  [{count}] {paper.title[:60]}...")
                if count >= 3:
                    break
            print(f"  Total: {count} papers")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fetchers())
