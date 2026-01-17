"""Demo AI provider for testing."""
from typing import Optional
import random
from app.ai.providers.base import AIProvider

class DemoProvider(AIProvider):
    """Demo provider that returns mock responses."""
    
    provider_name = "demo"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Return a mock completion."""
        
        # Check if this is a summarization request
        if "Summarize this scientific paper" in prompt:
            return """HEADLINE: Gene Therapy Breakthrough Offers New Hope
TAKEAWAY: Researchers have developed a novel delivery vector that increases the efficiency of gene therapy by 300%. This method significantly reduces immune response in patient trials.
WHY_MATTERS: This advancement overcomes a major hurdle in treating genetic disorders, potentially making therapies safer and more accessible.
KEY_TAKEAWAY_1_LABEL: Higher Efficiency
KEY_TAKEAWAY_1_TEXT: The new vector delivers therapeutic genes 3x more effectively than current standards.
KEY_TAKEAWAY_2_LABEL: Reduced Side Effects
KEY_TAKEAWAY_2_TEXT: Patients experienced significantly fewer immune reactions, a common complication in gene therapy.
KEY_TAKEAWAY_3_LABEL: Faster Treatment
KEY_TAKEAWAY_3_TEXT: The improved delivery speed could shorten treatment duration for patients.
TAGS: gene therapy, biotechnology, medicine"""

        # Check if this is an intro request
        if "Write a COMPREHENSIVE introduction" in prompt:
            return """Welcome to this week's Enhanced Science Digest! We are thrilled to bring you a collection of research that bridges the gap between biological discovery and technological innovation. From the precision of gene editing to the vast potential of quantum computing, this edition highlights how science is reshaping our future. The common thread in these papers is resilience—the ability of systems, both natural and engineered, to adapt and thrive. We hope these insights inspire you to see the connections in your own world."""

        # Check if this is a narrative request
        if "writing a connecting narrative" in prompt:
            return """The convergence of biology and technology is the standout theme of this week's research. Papers on CRISPR and mRNA vaccines demonstrate our growing mastery over the building blocks of life, offering new tools to combat disease. Simultaneously, breakthroughs in quantum computing and solar energy show how we are harnessing physics to solve computational and environmental challenges.

Interestingly, these fields are not developing in isolation. The tools of AI are accelerating drug discovery, while our understanding of biological systems is informing softer, more adaptive robotics. This interplay suggests a future where the boundaries between the organic and the synthetic become increasingly permeable, leading to solutions that are both powerful and sustainable.

As we face global challenges like climate change—also covered in this digest—this synthesis of disciplines will be crucial. The research suggests that by combining the efficiency of engineering with the adaptability of biology, we can create more resilient systems for a changing world."""

        # Check if this is a conclusion request
        if "Write a robust conclusion" in prompt:
            return """**The Big Picture**
- Precision medicine is advancing rapidly with new gene-editing tools.
- AI is accelerating scientific discovery across all fields.
- Interdisciplinary approaches are yielding the most impactful solutions.
- Sustainability is a core driver of innovation in energy and materials.

**Living It**
Take a moment this week to observe the intersection of nature and technology in your life. Perhaps it's the biometric sensor on your phone or the bio-based materials in your home. Consider how these innovations are interconnected. We encourage you to stay curious and keep exploring the science that shapes our daily reality. Thank you for reading!"""

        return "Demo response: AI processing complete."

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> str:
        """Return a mock image URL."""
        return "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&q=80&w=1000"
