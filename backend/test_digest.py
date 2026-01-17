"""Test digest creation with fetched papers."""
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_create_digest():
    """Test creating a digest from fetched papers."""
    print("="*70)
    print("TESTING DIGEST CREATION")
    print("="*70)

    # First, get the list of papers
    print("\n1. Fetching list of papers...")
    try:
        response = httpx.get(f"{BASE_URL}/papers/?limit=15", timeout=10)
        response.raise_for_status()
        data = response.json()
        papers = data["papers"]

        if not papers:
            print("[FAIL] No papers found. Run fetch first!")
            return

        print(f"[PASS] Found {len(papers)} papers")

        # Display papers
        print("\nAvailable papers:")
        for i, paper in enumerate(papers[:10], 1):
            print(f"  {i}. [{paper['id']}] {paper['title'][:60]}...")

        # Get paper IDs
        paper_ids = [p['id'] for p in papers[:10]]  # Use first 10 papers

    except Exception as e:
        print(f"[FAIL] Failed to get papers: {e}")
        return

    # Create digest
    print(f"\n2. Creating digest with {len(paper_ids)} papers...")

    payload = {
        "name": "Positive Psychology Research Digest",
        "paper_ids": paper_ids,
        "ai_provider": "gemini",
        "ai_model": "gemini-2.0-flash-exp",
        "summary_style": "newsletter",
        "generate_images": True
    }

    print(f"\nDigest payload:")
    print(f"  Name: {payload['name']}")
    print(f"  Papers: {len(payload['paper_ids'])} papers")
    print(f"  AI Provider: {payload['ai_provider']}")
    print(f"  AI Model: {payload['ai_model']}")
    print(f"  Style: {payload['summary_style']}")

    try:
        response = httpx.post(
            f"{BASE_URL}/digests/",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        digest = response.json()

        print(f"\n[PASS] Digest created successfully!")
        print(f"  Digest ID: {digest['id']}")
        print(f"  Name: {digest['name']}")
        print(f"  Status: {digest['status']}")

        # Get digest details
        print(f"\n3. Fetching digest details...")
        response = httpx.get(f"{BASE_URL}/digests/{digest['id']}", timeout=10)
        response.raise_for_status()
        full_digest = response.json()

        print(f"[PASS] Digest details retrieved")
        print(f"  Papers in digest: {len(full_digest.get('digest_papers', []))}")
        print(f"  Status: {full_digest['status']}")

        if full_digest.get('intro_text'):
            print(f"\nIntro text preview:")
            print(f"  {full_digest['intro_text'][:200]}...")

        return digest['id']

    except httpx.HTTPStatusError as e:
        print(f"\n[FAIL] HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\n[FAIL] Failed to create digest: {e}")
        return None


def test_list_digests():
    """List all digests."""
    print("\n" + "="*70)
    print("LISTING ALL DIGESTS")
    print("="*70)

    try:
        response = httpx.get(f"{BASE_URL}/digests/?limit=10", timeout=10)
        response.raise_for_status()
        data = response.json()

        digests = data["digests"]
        total = data["total"]

        print(f"\nTotal digests: {total}")

        if not digests:
            print("No digests found yet.")
            return

        for i, digest in enumerate(digests, 1):
            print(f"\n{i}. {digest['name']}")
            print(f"   ID: {digest['id']}")
            print(f"   Status: {digest['status']}")
            print(f"   Created: {digest['created_at']}")
            if digest.get('processed_at'):
                print(f"   Processed: {digest['processed_at']}")
            papers_count = len(digest.get('digest_papers', []))
            print(f"   Papers: {papers_count}")

    except Exception as e:
        print(f"[FAIL] Failed to list digests: {e}")


def main():
    """Main test flow."""
    print("\n" + "="*70)
    print("DIGEST CREATION TEST")
    print("="*70)

    # Create digest
    digest_id = test_create_digest()

    # List all digests
    test_list_digests()

    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)

    if digest_id:
        print(f"\n[SUCCESS] Created digest with ID: {digest_id}")
        print(f"Note: Digest processing happens in background.")
        print(f"Check status with: GET {BASE_URL}/digests/{digest_id}")
    else:
        print("\n[FAILED] Digest creation failed")


if __name__ == "__main__":
    main()
