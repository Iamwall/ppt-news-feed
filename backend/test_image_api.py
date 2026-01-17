"""Debug Gemini Image API Response."""
import asyncio
import httpx
import sys
sys.path.insert(0, ".")

async def test_api_directly():
    print("=" * 60)
    print("TESTING GEMINI IMAGE API DIRECTLY")
    print("=" * 60)
    
    from app.core.config import settings
    
    api_key = settings.google_api_key
    if not api_key:
        print("ERROR: No API key!")
        return
        
    model = "gemini-2.5-flash-image"
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    prompt = "A simple abstract blue wave pattern, modern scientific style."
    
    print(f"\n[API] Calling {model}...")
    print(f"[API] Prompt: {prompt}\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/models/{model}:generateContent",
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
            },
            timeout=120.0,
        )
        
        print(f"[API] Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[API] Error Response:\n{response.text[:1000]}")
            return
            
        data = response.json()
        
        # Check for candidates
        candidates = data.get("candidates", [])
        if not candidates:
            print(f"[API] No candidates in response: {data}")
            return
            
        parts = candidates[0].get("content", {}).get("parts", [])
        print(f"[API] Found {len(parts)} parts in response")
        
        for i, part in enumerate(parts):
            if "text" in part:
                print(f"[API] Part {i}: TEXT - {part['text'][:100]}...")
            elif "inlineData" in part:
                inline = part["inlineData"]
                mime = inline.get("mimeType", "unknown")
                data_len = len(inline.get("data", ""))
                print(f"[API] Part {i}: IMAGE - {mime}, {data_len} bytes")
                
                # Save image
                import base64
                from pathlib import Path
                
                Path("./generated_images").mkdir(exist_ok=True)
                img_bytes = base64.b64decode(inline["data"])
                
                ext = "png" if "png" in mime else "jpg"
                filepath = f"./generated_images/test_image.{ext}"
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                print(f"[API] ✓ Saved to: {filepath}")
            else:
                print(f"[API] Part {i}: UNKNOWN - {list(part.keys())}")

if __name__ == "__main__":
    asyncio.run(test_api_directly())
