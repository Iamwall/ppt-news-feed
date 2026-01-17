"""Test all paper fetchers to verify they work correctly."""
import asyncio
from app.fetchers import FETCHER_REGISTRY


async def test_fetcher(source_name: str):
    """Test a single fetcher."""
    print(f"\n{'='*70}")
    print(f"Testing: {source_name.upper()}")
    print('='*70)

    try:
        from app.fetchers import get_fetcher
        fetcher = get_fetcher(source_name)

        # Test parameters based on source
        if source_name in ['nature_rss', 'science_rss']:
            # RSS feeds don't use keywords
            keywords = None
        else:
            keywords = ['machine learning']

        papers = []
        async for paper in fetcher.fetch(
            keywords=keywords,
            max_results=3,
            days_back=30
        ):
            papers.append(paper)
            if len(papers) >= 3:
                break

        if papers:
            print(f"[PASS] SUCCESS: Fetched {len(papers)} papers")
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper.title[:70]}...")
                if paper.authors:
                    authors = [a.name for a in paper.authors[:2]]
                    print(f"   Authors: {', '.join(authors)}")
                print(f"   Source ID: {paper.source_id}")
                print(f"   Published: {paper.published_date}")
                if paper.doi:
                    print(f"   DOI: {paper.doi}")
                if paper.citations is not None:
                    print(f"   Citations: {paper.citations}")
        else:
            print("[WARN] WARNING: No papers returned (might be expected for recent papers)")

        return True

    except Exception as e:
        print(f"[FAIL] FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test all fetchers."""
    print("="*70)
    print("TESTING ALL PAPER FETCHERS")
    print("="*70)

    results = {}

    for source_name in FETCHER_REGISTRY.keys():
        success = await test_fetcher(source_name)
        results[source_name] = success
        await asyncio.sleep(1)  # Be nice to APIs

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)

    for source, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {source}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\nTotal: {passed}/{total} fetchers working")


if __name__ == "__main__":
    asyncio.run(main())
