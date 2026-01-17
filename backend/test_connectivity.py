"""Quick test to diagnose fetch issues."""
import asyncio
import httpx

async def test_sources():
    print("Testing external API connectivity...\n")
    
    sources = [
        ("PubMed", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=test&retmax=1&retmode=json"),
        ("arXiv", "https://export.arxiv.org/api/query?search_query=all:test&max_results=1"),
        ("bioRxiv", "https://api.biorxiv.org/details/biorxiv/2024-01-01/2024-01-10/0"),
        ("medRxiv", "https://api.biorxiv.org/details/medrxiv/2024-01-01/2024-01-10/0"),
    ]
    
    async with httpx.AsyncClient() as client:
        for name, url in sources:
            try:
                print(f"Testing {name}...", end=" ")
                response = await asyncio.wait_for(
                    client.get(url, timeout=15.0),
                    timeout=20.0
                )
                print(f"✓ Status {response.status_code}, {len(response.content)} bytes")
            except asyncio.TimeoutError:
                print(f"✗ TIMEOUT (>20s)")
            except Exception as e:
                print(f"✗ ERROR: {e}")

    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(test_sources())
