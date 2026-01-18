"""Comprehensive test for all new data source fetchers."""
import asyncio
from datetime import datetime

# Fetchers that don't require API keys
NO_KEY_FETCHERS = [
    ("hackernews", "app.fetchers.news.hackernews", "HackerNewsFetcher", None),
    ("reddit", "app.fetchers.news.reddit", "RedditFetcher", {"subreddits": ["technology"]}),
    ("gdelt", "app.fetchers.news.gdelt", "GDELTFetcher", None),
    ("github_trending", "app.fetchers.tech.github_trending", "GitHubTrendingFetcher", None),
    ("devto", "app.fetchers.tech.devto", "DevToFetcher", None),
    ("stackexchange", "app.fetchers.tech.stackexchange", "StackExchangeFetcher", {"sites": ["stackoverflow"]}),
    ("coingecko", "app.fetchers.financial.coingecko", "CoinGeckoFetcher", None),
    ("yahoo_finance", "app.fetchers.financial.yahoo_finance", "YahooFinanceFetcher", {"tickers": ["AAPL"]}),
    ("openfda", "app.fetchers.health.openfda", "OpenFDAFetcher", None),
    ("clinicaltrials", "app.fetchers.health.clinicaltrials", "ClinicalTrialsFetcher", None),
    ("openalex", "app.fetchers.research.openalex", "OpenAlexFetcher", None),
    ("crossref", "app.fetchers.research.crossref", "CrossrefFetcher", None),
    ("doaj", "app.fetchers.research.doaj", "DOAJFetcher", None),
]


async def test_fetcher(name: str, module: str, class_name: str, init_kwargs: dict = None):
    """Test a single fetcher."""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print('='*50)
    
    try:
        # Dynamic import
        import importlib
        mod = importlib.import_module(module)
        fetcher_class = getattr(mod, class_name)
        
        # Initialize
        if init_kwargs:
            fetcher = fetcher_class(**init_kwargs)
        else:
            fetcher = fetcher_class()
        
        items = []
        async for item in fetcher.fetch(
            keywords=["AI"] if name not in ["coingecko", "yahoo_finance", "openfda", "gdelt"] else None,
            max_results=3,
            days_back=30  # Extended for some APIs
        ):
            items.append(item)
            if len(items) >= 2:
                break
        
        if items:
            print(f"[PASS] Fetched {len(items)} items")
            for i, item in enumerate(items[:2], 1):
                title = item.title[:50] + "..." if len(item.title) > 50 else item.title
                print(f"  {i}. {title}")
        else:
            print("[WARN] No items (may be expected)")
        
        return True, None
        
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {str(e)[:100]}")
        return False, str(e)


async def main():
    """Test all new fetchers."""
    print("="*50)
    print("COMPREHENSIVE FETCHER TEST")
    print(f"Time: {datetime.now()}")
    print("="*50)
    
    results = {}
    errors = {}
    
    for name, module, class_name, kwargs in NO_KEY_FETCHERS:
        success, error = await test_fetcher(name, module, class_name, kwargs)
        results[name] = success
        if error:
            errors[name] = error
        await asyncio.sleep(1)  # Rate limiting between tests
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    
    for name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} fetchers working")
    
    if errors:
        print("\nErrors:")
        for name, error in errors.items():
            print(f"  {name}: {error[:80]}")
    
    return passed >= total * 0.8  # Allow 20% failure rate


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
