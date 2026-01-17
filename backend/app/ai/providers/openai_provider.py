"""OpenAI provider implementation."""
from typing import Optional

from app.ai.providers.base import AIProvider
from app.core.config import settings

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None


class OpenAIProvider(AIProvider):
    provider_name = "openai"
    
    def __init__(self, model=None):
        self.model = model or "gpt-4o"
        if OPENAI_AVAILABLE and settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
    
    async def complete(self, prompt, system_prompt=None, max_tokens=1000, temperature=0.7):
        if not self.client:
            return self._demo_complete(prompt)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await self.client.chat.completions.create(
            model=self.model, messages=messages, max_tokens=max_tokens, temperature=temperature
        )
        return response.choices[0].message.content
    
    async def generate_image(self, prompt, size="1024x1024", style="natural"):
        if not self.client:
            return ""
        response = await self.client.images.generate(
            model="dall-e-3", prompt=prompt, size=size, style=style, quality="standard", n=1
        )
        return response.data[0].url
    
    def _demo_complete(self, prompt):
        if "HEADLINE" in prompt:
            return "HEADLINE: Research Finding\nTAKEAWAY: Demo summary.\nWHY_MATTERS: Demo.\nTAGS: demo"
        return "Demo response"
