"""Test Gemini Image Generation with correct model."""
import asyncio
import sys
sys.path.insert(0, ".")

async def test_image_generation():
    print("=" * 60)
    print("TESTING GEMINI IMAGE GENERATION")
    print("=" * 60)
    
    from app.core.config import settings
    from app.ai.providers.gemini_provider import GeminiProvider
    
    print(f"\n[CONFIG] GOOGLE_API_KEY: {'SET' if settings.google_api_key else 'NOT SET'}")
    
    if not settings.google_api_key:
        print("ERROR: No Google API key configured!")
        return
    
    provider = GeminiProvider()
    
    # Test prompt
    prompt = """A beautiful abstract visualization of neural pathways in the brain,
showing glowing blue and purple connections, modern scientific illustration style,
clean composition suitable for a newsletter header."""
    
    print(f"\n[TEST] Generating image with prompt:")
    print(f"  '{prompt[:80]}...'\n")
    print("[TEST] Using model: gemini-2.5-flash-image")
    print("[TEST] This may take 30-60 seconds...\n")
    
    try:
        image_path = await provider.generate_image(
            prompt=prompt,
            size="1024x1024",
            style="scientific"
        )
        
        if image_path:
            print(f"\n✓ SUCCESS! Image saved to: {image_path}")
            print(f"\nYou can view it at: http://localhost:8000{image_path}")
        else:
            print("\n✗ FAILED: No image was generated. Check server logs for errors.")
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_generation())
