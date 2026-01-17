"""Anthropic Claude provider implementation."""
from typing import Optional

from app.ai.providers.base import AIProvider
from app.core.config import settings

# Try to import Anthropic SDK - may not be installed in demo mode
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""
    
    provider_name = "anthropic"
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or "claude-sonnet-4-20250514"
        if ANTHROPIC_AVAILABLE and settings.anthropic_api_key:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            self.client = None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion using Claude."""
        if not self.client:
            return "Demo response - Anthropic API key not configured"
        
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful scientific writing assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        return message.content[0].text
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> str:
        """Claude doesn't support image generation, falls back to Gemini."""
        from app.ai.providers.gemini_provider import GeminiProvider
        gemini = GeminiProvider()
        return await gemini.generate_image(prompt, size, style)
