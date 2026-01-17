"""Test PubMed fetcher abstract extraction."""
import asyncio
from app.fetchers import PubMedFetcher


async def test():
    f = PubMedFetcher()
    papers = []
    
    async for p in f.fetch(keywords=['psychology'], max_results=5, days_back=7):
        papers.append(p)
        print(f"Title: {p.title[:70]}...")
        if p.abstract:
            print(f"Abstract: {p.abstract[:100]}...")
        else:
            print("Abstract: MISSING")
        print()
    
    print(f"\nFetched {len(papers)} papers")
    with_abstract = sum(1 for p in papers if p.abstract)
    print(f"With abstract: {with_abstract}/{len(papers)}")


if __name__ == "__main__":
    asyncio.run(test())
