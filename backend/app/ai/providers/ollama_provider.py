"""Ollama local model provider implementation."""
from typing import Optional

from app.ai.providers.base import AIProvider
from app.core.config import settings

# Try to import httpx - should be installed
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class OllamaProvider(AIProvider):
    """Ollama local model provider."""
    
    provider_name = "ollama"
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or "llama3"
        self.base_url = settings.ollama_base_url
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using local Ollama model."""
        if not HTTPX_AVAILABLE:
            return "Demo response - httpx not installed"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                        },
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                data = response.json()
            
            return data.get("response", "")
        except Exception as e:
            return f"Ollama not available: {e}"
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> str:
        """Ollama doesn't support image generation, falls back to Gemini."""
        from app.ai.providers.gemini_provider import GeminiProvider
        gemini = GeminiProvider()
        return await gemini.generate_image(prompt, size, style)
