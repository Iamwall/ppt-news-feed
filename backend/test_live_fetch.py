"""Test live fetching of papers on positive psychology."""
import httpx
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5)
        print(f"Health check: {response.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_sources():
    """List available sources."""
    print("\n" + "="*70)
    print("AVAILABLE SOURCES")
    print("="*70)
    try:
        response = httpx.get(f"{BASE_URL}/fetch/sources", timeout=5)
        sources = response.json()["sources"]
        for source in sources:
            status = source.get("status", "available")
            status_emoji = "[X]" if status == "unavailable" else "[OK]"
            print(f"{status_emoji} {source['id']:20} - {source['name']}")
        return sources
    except Exception as e:
        print(f"Failed to get sources: {e}")
        return []

def start_fetch():
    """Start fetching papers on positive psychology."""
    print("\n" + "="*70)
    print("FETCHING PAPERS ON: Positive Psychology")
    print("="*70)

    # Select diverse sources
    sources_to_use = [
        "pubmed",
        "arxiv",
        "plos",
        "nature_rss",
        "science_rss",
    ]

    payload = {
        "sources": sources_to_use,
        "keywords": ["positive psychology", "well-being", "happiness"],
        "max_results": 20,
        "days_back": 30
    }

    print(f"\nSources: {', '.join(sources_to_use)}")
    print(f"Keywords: {', '.join(payload['keywords'])}")
    print(f"Time range: Last {payload['days_back']} days")
    print(f"Max results: {payload['max_results']} papers\n")

    try:
        response = httpx.post(f"{BASE_URL}/fetch/", json=payload, timeout=10)
        result = response.json()
        job_id = result["job_id"]
        print(f"Fetch job started! Job ID: {job_id}")
        return job_id
    except Exception as e:
        print(f"Failed to start fetch: {e}")
        return None

def monitor_fetch(job_id):
    """Monitor fetch progress."""
    print("\nMonitoring fetch progress...")
    print("-" * 70)

    while True:
        try:
            response = httpx.get(f"{BASE_URL}/fetch/status/{job_id}", timeout=5)
            status = response.json()

            current_status = status["status"]
            progress = status["progress"]
            current_source = status.get("current_source", "N/A")

            print(f"\rStatus: {current_status:12} | Progress: {progress:3}% | Source: {current_source:20}", end="", flush=True)

            if current_status in ["completed", "failed"]:
                print()  # New line
                return status

            time.sleep(2)
        except Exception as e:
            print(f"\nError monitoring: {e}")
            return None

def display_results(status):
    """Display fetch results."""
    print("\n" + "="*70)
    print("FETCH RESULTS")
    print("="*70)

    print(f"Status: {status['status']}")
    print(f"Papers fetched: {status['papers_fetched']}")
    print(f"Papers new: {status['papers_new']}")
    print(f"Papers updated: {status['papers_updated']}")

    if status.get('errors'):
        print(f"\nErrors encountered:")
        for error in status['errors']:
            print(f"  - {error}")

    # Get papers
    print("\n" + "="*70)
    print("FETCHED PAPERS")
    print("="*70)

    try:
        response = httpx.get(f"{BASE_URL}/papers/?limit=10", timeout=10)
        data = response.json()
        papers = data["papers"]

        if not papers:
            print("No papers found yet.")
            return

        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Source: {paper['source']}")
            print(f"   Published: {paper.get('published_date', 'Unknown')}")
            if paper.get('credibility_score'):
                print(f"   Credibility: {paper['credibility_score']}/100")
            if paper.get('abstract'):
                abstract = paper['abstract'][:200] + "..." if len(paper['abstract']) > 200 else paper['abstract']
                print(f"   Abstract: {abstract}")

    except Exception as e:
        print(f"Failed to get papers: {e}")

def main():
    """Main test flow."""
    print("="*70)
    print("LIVE FETCH TEST: Positive Psychology")
    print("="*70)

    # Check health
    if not test_health():
        print("Server is not responding. Make sure it's running!")
        return

    # List sources
    sources = test_sources()
    if not sources:
        print("Failed to get sources!")
        return

    # Start fetch
    job_id = start_fetch()
    if not job_id:
        print("Failed to start fetch!")
        return

    # Monitor progress
    final_status = monitor_fetch(job_id)
    if not final_status:
        print("Failed to monitor fetch!")
        return

    # Display results
    display_results(final_status)

    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)

if __name__ == "__main__":
    main()
