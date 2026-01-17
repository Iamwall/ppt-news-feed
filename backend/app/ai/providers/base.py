"""Base AI provider interface."""
from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    provider_name: str = "base"
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion for the given prompt."""
        pass
    
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> str:
        """Generate an image and return the URL or file path."""
        pass


def get_ai_provider(provider: str, model: Optional[str] = None) -> AIProvider:
    """Factory function to get AI provider instance."""
    from app.ai.providers.openai_provider import OpenAIProvider
    from app.ai.providers.anthropic_provider import AnthropicProvider
    from app.ai.providers.ollama_provider import OllamaProvider
    from app.ai.providers.gemini_provider import GeminiProvider
    from app.ai.providers.groq_provider import GroqProvider
    from app.ai.providers.demo_provider import DemoProvider
    
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "demo": DemoProvider,
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown AI provider: {provider}")
    
    return providers[provider](model=model)
