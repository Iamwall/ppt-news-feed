"""AI-powered image generation for papers."""
import os
from typing import Optional, List

from app.ai.providers.base import get_ai_provider
from app.ai.providers.gemini_provider import GeminiProvider
from app.models.paper import Paper
from app.core.config import settings


class ImageGenerator:
    """Service for generating images for papers."""
    
    def __init__(self, provider: str = None):
        self.provider_name = provider or settings.default_image_provider
    
    async def generate(self, paper: Paper) -> str:
        """Generate an image for a paper and return the file path."""
        
        # Generate image prompt from paper content
        prompt = await self._create_prompt(paper)
        paper.image_prompt = prompt
        
        # Generate image
        try:
            if self.provider_name == "gemini":
                provider = GeminiProvider()
            elif self.provider_name == "dalle":
                from app.ai.providers.openai_provider import OpenAIProvider
                provider = OpenAIProvider()
            else:
                # Default to Gemini
                provider = GeminiProvider()
            
            image_path = await provider.generate_image(
                prompt=prompt,
                size="1024x1024",
                style="natural",
            )
            
            return image_path
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return ""
    
    async def _create_prompt(self, paper: Paper) -> str:
        """Create an image generation prompt from paper content."""

        # Use configured AI provider for prompt generation
        from app.core.config import settings
        ai = get_ai_provider(settings.default_ai_provider, settings.default_ai_model)

        # Use summary if available for better context
        context = f"""TITLE: {paper.title}

HEADLINE: {paper.summary_headline or ""}

KEY FINDING: {paper.summary_takeaway or ""}

ABSTRACT: {(paper.abstract or "")[:400]}"""

        prompt = f"""Create a vivid image generation prompt for an INFORMATIVE scientific infographic in Leonardo da Vinci's technical sketch style.

RESEARCH CONTEXT:
{context}

The image must be EDUCATIONAL - a viewer should understand the key finding just by looking at it.

CONTENT REQUIREMENTS (most important):
- Central visual metaphor representing the main finding
- 3-4 labeled diagram elements showing key concepts (use elegant hand-lettering)
- Visual representation of the data/statistics (simple icons, comparisons, before/after)
- Arrows and flow lines showing cause-and-effect relationships
- Small numbered annotations (1, 2, 3) showing process steps or sequence
- Icons or symbols representing practical applications

STYLE REQUIREMENTS:
- Da Vinci renaissance sketch style: sepia/brown ink on aged parchment paper
- Hand-drawn technical illustration with cross-hatching and fine linework
- Anatomical precision applied to the scientific concepts
- Vintage scientific notebook aesthetic
- Labels should be in English and readable (not mirror-writing)

The illustration should teach the research finding visually, like Da Vinci explaining a discovery in his notebook.

Return ONLY the image prompt (200-250 words), describing specific visual elements that convey the research finding."""

        response = await ai.complete(prompt, max_tokens=300, temperature=0.8)

        # Clean up and enhance the prompt
        image_prompt = response.strip()

        # Add Da Vinci style modifiers
        image_prompt = f"{image_prompt}. Leonardo da Vinci style technical sketch, sepia ink on aged parchment, renaissance scientific illustration, detailed cross-hatching, anatomical precision, vintage scientific diagram with arrows and annotations, hand-drawn infographic elements, masterful linework, museum quality scientific art."

        return image_prompt

    async def generate_summary_infographic(self, papers: List[Paper], digest_name: str) -> str:
        """Generate a summary infographic for the entire digest's Final Thoughts section."""

        # Create the summary prompt
        prompt = await self._create_summary_prompt(papers, digest_name)

        # Generate image
        try:
            if self.provider_name == "gemini":
                provider = GeminiProvider()
            elif self.provider_name == "dalle":
                from app.ai.providers.openai_provider import OpenAIProvider
                provider = OpenAIProvider()
            else:
                provider = GeminiProvider()

            image_path = await provider.generate_image(
                prompt=prompt,
                size="1024x1024",
                style="natural",
            )

            return image_path

        except Exception as e:
            print(f"Error generating summary infographic: {e}")
            return ""

    async def _create_summary_prompt(self, papers: List[Paper], digest_name: str) -> str:
        """Create an image generation prompt for a digest summary infographic."""

        from app.core.config import settings
        ai = get_ai_provider(settings.default_ai_provider, settings.default_ai_model)

        # Gather key insights from all papers
        insights = []
        topics = []
        for paper in papers:
            if paper.summary_headline:
                insights.append(f"- {paper.summary_headline}")
            if paper.tags:
                topics.extend(paper.tags)

        unique_topics = list(set(topics))[:8]
        insights_text = "\n".join(insights[:6])
        topics_text = ", ".join(unique_topics)

        prompt = f"""Create a vivid image generation prompt for an INFORMATIVE SUMMARY INFOGRAPHIC in Leonardo da Vinci's technical sketch style.

This infographic must TEACH the viewer about ALL key findings from a science digest newsletter.

DIGEST: "{digest_name}"
TOPICS COVERED: {topics_text}

KEY FINDINGS TO VISUALIZE:
{insights_text}

CONTENT REQUIREMENTS (most important):
- Central hub showing the unifying theme with a clear TITLE label
- Separate visual sections for EACH key finding (like chapters in a visual book)
- Each section has: icon/symbol + short text label + visual representation of the data
- Numbered list (1, 2, 3...) showing the key takeaways readers should remember
- Arrows connecting related concepts showing how findings reinforce each other
- "Action Items" section with icons representing practical applications
- Visual summary statistics or comparisons where relevant

STYLE REQUIREMENTS:
- Da Vinci renaissance master sketch: sepia/brown ink on aged parchment
- Hand-drawn infographic elements with elegant hand-lettered labels (readable English)
- Visual hierarchy: main theme large in center, supporting findings around it
- Cross-hatching shading and fine renaissance linework
- Icons and symbols should be clear and meaningful

A reader should be able to understand ALL the newsletter's main points just by studying this image for 30 seconds.

Return ONLY the image prompt (250-300 words), describing specific visual elements that summarize each finding."""

        response = await ai.complete(prompt, max_tokens=400, temperature=0.8)

        image_prompt = response.strip()

        # Add Da Vinci style modifiers for summary infographic
        image_prompt = f"{image_prompt}. Leonardo da Vinci style master diagram, sepia ink on aged parchment, renaissance scientific synthesis illustration, interconnected concept map, visual knowledge hierarchy, detailed cross-hatching, flowing connection lines and arrows, hand-drawn infographic summarizing multiple topics, anatomical precision applied to abstract concepts, museum quality scientific art, unified visual narrative."

        return image_prompt
