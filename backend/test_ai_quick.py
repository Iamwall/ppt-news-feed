"""Quick test to check what AI provider returns."""
import asyncio
import sys
sys.path.insert(0, ".")

async def test_ai():
    from app.core.config import settings
    from app.ai.providers.base import get_ai_provider
    
    print(f"DEMO_MODE: {settings.demo_mode}")
    print(f"DEFAULT_AI_PROVIDER: {settings.default_ai_provider}")
    print(f"GROQ_API_KEY: {'SET' if settings.groq_api_key else 'NOT SET'}")
    
    provider = get_ai_provider(settings.default_ai_provider)
    print(f"\nProvider class: {provider.__class__.__name__}")
    print(f"Provider API key set: {'Yes' if provider.api_key else 'No'}")
    
    response = await provider.complete(
        "Say 'Hello, I am working!' in exactly those words.",
        max_tokens=20
    )
    
    print(f"\nAI Response: {response}")
    
    if "demo" in response.lower():
        print("\n❌ PROBLEM: Still getting demo response!")
    else:
        print("\n✓ AI is working correctly!")

if __name__ == "__main__":
    asyncio.run(test_ai())
