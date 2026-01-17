"""Groq provider implementation - fast LLM inference."""
from typing import Optional
import httpx

from app.ai.providers.base import AIProvider
from app.core.config import settings


class GroqProvider(AIProvider):
    """Groq provider for fast LLM inference."""
    
    provider_name = "groq"
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or "llama-3.3-70b-versatile"
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using Groq."""
        if not self.api_key:
            return "Groq API key not configured"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        return data["choices"][0]["message"]["content"]
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> str:
        """Groq doesn't support images, fallback to Gemini."""
        from app.ai.providers.gemini_provider import GeminiProvider
        gemini = GeminiProvider()
        return await gemini.generate_image(prompt, size, style)
