"""Test enhanced digest with interconnected narrative and key takeaways."""
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_enhanced_digest():
    """Test the enhanced digest creation with new features."""
    print("="*80)
    print("TESTING ENHANCED DIGEST FEATURES")
    print("="*80)

    # Get papers
    print("\n1. Fetching papers...")
    try:
        response = httpx.get(f"{BASE_URL}/papers/?limit=5", timeout=10)
        response.raise_for_status()
        data = response.json()
        papers = data["papers"]

        if not papers:
            print("[FAIL] No papers found. Fetch some papers first!")
            return

        print(f"[PASS] Found {len(papers)} papers")
        paper_ids = [p['id'] for p in papers]

    except Exception as e:
        print(f"[FAIL] Failed to get papers: {e}")
        return

    # Create enhanced digest
    print(f"\n2. Creating enhanced digest with {len(paper_ids)} papers...")

    payload = {
        "name": "Enhanced Digest - Interconnected Findings",
        "paper_ids": paper_ids,
        "ai_provider": "gemini",
        "ai_model": "gemini-2.0-flash-exp",
        "summary_style": "newsletter",
        "generate_images": True
    }

    try:
        response = httpx.post(f"{BASE_URL}/digests/", json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        digest_id = result["id"]

        print(f"[PASS] Digest created (ID: {digest_id})")
        print("       Status:", result["status"])

    except Exception as e:
        print(f"[FAIL] Failed to create digest: {e}")
        return

    # Wait for processing
    print(f"\n3. Waiting for digest processing...")
    print("   This may take a few minutes as AI generates summaries and connections...\n")

    max_wait = 120  # 2 minutes
    interval = 5
    elapsed = 0

    while elapsed < max_wait:
        try:
            response = httpx.get(f"{BASE_URL}/digests/{digest_id}", timeout=10)
            response.raise_for_status()
            digest = response.json()

            status = digest["status"]
            print(f"   [{elapsed}s] Status: {status}")

            if status == "completed":
                print("\n[PASS] Digest processing completed!")
                break
            elif status == "failed":
                print(f"\n[FAIL] Digest processing failed: {digest.get('error_message', 'Unknown error')}")
                return

            time.sleep(interval)
            elapsed += interval

        except Exception as e:
            print(f"   Error checking status: {e}")
            time.sleep(interval)
            elapsed += interval

    if elapsed >= max_wait:
        print(f"\n[WARN] Timeout after {max_wait}s - digest may still be processing")
        return

    # Display results
    print("\n" + "="*80)
    print("DIGEST RESULTS")
    print("="*80)

    try:
        response = httpx.get(f"{BASE_URL}/digests/{digest_id}", timeout=10)
        response.raise_for_status()
        digest = response.json()

        # Check intro
        print("\n[INTRO TEXT]")
        if digest.get("intro_text"):
            print(f"{digest['intro_text']}\n")
            print(f"✓ Intro generated ({len(digest['intro_text'])} chars)")
        else:
            print("✗ No intro text")

        # Check connecting narrative
        print("\n[CONNECTING NARRATIVE]")
        if digest.get("connecting_narrative"):
            # Show first 300 chars
            narrative = digest['connecting_narrative']
            preview = narrative[:300] + "..." if len(narrative) > 300 else narrative
            print(f"{preview}\n")
            print(f"✓ Connecting narrative generated ({len(narrative)} chars)")
        else:
            print("✗ No connecting narrative")

        # Check papers with key takeaways
        print("\n[PAPERS & KEY TAKEAWAYS]")
        digest_papers = digest.get("digest_papers", [])

        for i, dp in enumerate(digest_papers, 1):
            paper = dp.get("paper", {})
            print(f"\nPaper {i}: {paper.get('title', 'Unknown')[:60]}...")
            print(f"  Headline: {paper.get('summary_headline', 'N/A')}")

            key_takeaways = paper.get('key_takeaways', [])
            if key_takeaways:
                print(f"  Key Takeaways ({len(key_takeaways)}):")
                for j, takeaway in enumerate(key_takeaways, 1):
                    print(f"    {j}. {takeaway}")
                print("  ✓ Key takeaways present")
            else:
                print("  ✗ No key takeaways")

            if paper.get('image_path'):
                print(f"  ✓ Image generated: {paper['image_path']}")
            else:
                print("  ○ No image yet")

        # Check conclusion
        print("\n[CONCLUSION TEXT]")
        if digest.get("conclusion_text"):
            print(f"{digest['conclusion_text']}\n")
            print(f"✓ Conclusion generated ({len(digest['conclusion_text'])} chars)")
        else:
            print("✗ No conclusion text")

        # Summary
        print("\n" + "="*80)
        print("FEATURE CHECKLIST")
        print("="*80)
        features = [
            ("Intro Text", bool(digest.get("intro_text"))),
            ("Connecting Narrative", bool(digest.get("connecting_narrative"))),
            ("Conclusion Text", bool(digest.get("conclusion_text"))),
            ("Papers Processed", len(digest_papers) > 0),
            ("Key Takeaways", any(p.get("paper", {}).get("key_takeaways") for p in digest_papers)),
            ("AI Summaries", any(p.get("paper", {}).get("summary_headline") for p in digest_papers)),
        ]

        for feature, present in features:
            status = "✓" if present else "✗"
            print(f"{status} {feature}")

        success_count = sum(1 for _, present in features if present)
        print(f"\nScore: {success_count}/{len(features)} features working")

        if success_count == len(features):
            print("\n🎉 All enhanced features are working!")
        elif success_count >= len(features) - 1:
            print("\n✅ Most features working - excellent!")
        else:
            print(f"\n⚠️  Some features need attention ({success_count}/{len(features)} working)")

    except Exception as e:
        print(f"[FAIL] Error retrieving digest: {e}")


if __name__ == "__main__":
    test_enhanced_digest()
