"""Google Gemini provider for image generation."""
import uuid
from typing import Optional
from pathlib import Path

from app.ai.providers.base import AIProvider
from app.core.config import settings

# Try to import httpx
try:
    import httpx
    import base64
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class GeminiProvider(AIProvider):
    """Google Gemini provider (primarily for image generation)."""
    
    provider_name = "gemini"
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or "gemini-2.0-flash-exp"
        self.api_key = settings.google_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using Gemini."""
        if not HTTPX_AVAILABLE or not self.api_key:
            return "Demo response - Gemini API not configured"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "maxOutputTokens": max_tokens,
                            "temperature": temperature,
                        },
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
            
            # Extract text from response
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception:
            pass
        
        return ""
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> str:
        """Generate image using Gemini 2.5 Flash Image model."""
        if not HTTPX_AVAILABLE or not self.api_key:
            print("[Gemini Image] API not available or no API key")
            return ""  # No image in demo mode

        # Use gemini-2.5-flash-image for image generation (dedicated image model)
        model = "gemini-2.5-flash-image"

        # The prompt already contains full Da Vinci style instructions from image_gen.py
        # Just add minimal framing to ensure quality output
        enhanced_prompt = f"""Create a detailed scientific illustration for a research newsletter.

{prompt}

CRITICAL REQUIREMENTS:
- Style: {style}, professional, museum-quality
- Make it INFORMATIVE: Include visual representations of key concepts, data relationships, and scientific processes
- Add LABELED DIAGRAMS: Use elegant hand-lettered labels (in English) to identify important elements
- Show CAUSE & EFFECT: Use arrows, flow lines, and numbered sequences to show relationships
- Include VISUAL DATA: Represent key statistics, comparisons, or findings as simple visual charts/icons
- Create VISUAL HIERARCHY: Main concept in center, supporting details around it
- The viewer should LEARN something just by looking at the image"""
        
        try:
            print(f"[Gemini Image] Generating image with model {model}...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": enhanced_prompt}]}],
                        "generationConfig": {
                            "responseModalities": ["image", "text"],
                        },
                    },
                    timeout=120.0,
                )
                
                if response.status_code != 200:
                    print(f"[Gemini Image] API error: {response.status_code} - {response.text[:200]}")
                    return ""
                
                data = response.json()
            
            # Extract image from response
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    inline_data = part.get("inlineData")
                    if inline_data:
                        mime_type = inline_data.get("mimeType", "image/png")
                        image_data = inline_data.get("data")
                        if image_data:
                            print(f"[Gemini Image] Image generated successfully ({mime_type})")
                            return await self._save_image(image_data, mime_type)
            
            print("[Gemini Image] No image in response")
            
        except Exception as e:
            print(f"[Gemini Image] Error: {e}")
            import traceback
            traceback.print_exc()
        
        return ""
    
    async def _save_image(self, base64_data: str, mime_type: str = "image/png") -> str:
        """Save base64 image data to file."""
        import base64
        
        # Determine file extension from mime type
        ext_map = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
        ext = ext_map.get(mime_type, "png")
        
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = Path(settings.generated_images_dir) / filename
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Decode and save
        image_bytes = base64.b64decode(base64_data)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        print(f"[Gemini Image] Saved to {filepath}")
        
        # Return relative path for serving
        return f"/static/images/{filename}"
