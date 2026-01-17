"""AI-powered paper summarization."""
from dataclasses import dataclass
from typing import List, Optional

from app.ai.providers.base import get_ai_provider
from app.models.paper import Paper


@dataclass
class PaperSummary:
    """Summary output for a paper."""
    headline: str
    takeaway: str
    why_matters: str
    key_takeaways: List[str]  # 3 key takeaways
    tags: List[str]


class Summarizer:
    """AI-powered paper summarization service."""

    def __init__(self, provider: str = "gemini", model: Optional[str] = None):
        self.provider = get_ai_provider(provider, model)
    
    async def summarize(
        self,
        paper: Paper,
        style: str = "newsletter",
    ) -> PaperSummary:
        """Generate summary for a paper."""
        
        style_instructions = self._get_style_instructions(style)

        # Handle authors - could be list or set
        authors_list = list(paper.authors) if paper.authors else []
        authors_str = ", ".join(a.name for a in authors_list[:5]) if authors_list else "Unknown"

        prompt = f"""Summarize this scientific paper for a newsletter audience.

TITLE: {paper.title}

ABSTRACT: {paper.abstract or "No abstract available."}

JOURNAL: {paper.journal or "Unknown"}
AUTHORS: {authors_str}
{"(Preprint - not peer reviewed)" if paper.is_preprint else ""}

{style_instructions}

Provide your response in this exact format:
HEADLINE: [A catchy, informative headline in 10-15 words]
TAKEAWAY: [2-3 sentences explaining the key finding and context]
WHY_MATTERS: [1-2 sentences on broader implications for science and society]
KEY_TAKEAWAY_1_LABEL: [Short catchy 2-5 word label for the first insight]
KEY_TAKEAWAY_1_TEXT: [First key insight - specific, actionable advice or fact the reader can apply to their life]
KEY_TAKEAWAY_2_LABEL: [Short catchy 2-5 word label for the second insight]
KEY_TAKEAWAY_2_TEXT: [Second key insight - specific, actionable advice or fact the reader can apply to their life]
KEY_TAKEAWAY_3_LABEL: [Short catchy 2-5 word label for the third insight]
KEY_TAKEAWAY_3_TEXT: [Third key insight - specific, actionable advice or fact the reader can apply to their life]
TAGS: [comma-separated list of 3-5 topic tags]"""

        system_prompt = """You are an expert science communicator who makes complex research accessible and applicable to daily life. 
You write engaging, accurate summaries that capture the essence of scientific findings.
Focus on practical utility: how can this knowledge improve the reader's life, health, or understanding of the world?
Always maintain scientific accuracy while making content engaging for general audiences."""

        response = await self.provider.complete(
            prompt,
            system_prompt=system_prompt,
            max_tokens=600,
            temperature=0.7,
        )
        
        return self._parse_summary(response)
    
    def _get_style_instructions(self, style: str) -> str:
        """Get style-specific instructions."""
        styles = {
            "newsletter": """Write in an engaging, accessible style suitable for a general science newsletter.
Use clear language that educated non-specialists can understand.
Focus on the "so what?" - why should readers care?
Highlight practical applications and actionable advice where possible.""",
            
            "technical": """Write in a precise, technical style for expert readers.
Include methodology details and statistical significance where relevant.
Assume familiarity with domain-specific terminology.""",
            
            "layperson": """Write in simple, everyday language for general public.
Avoid all jargon - explain any technical terms.
Use analogies and relatable examples where possible.
Focus on practical implications for daily life and wellness.""",
        }
        
        return styles.get(style, styles["newsletter"])
    
    def _parse_summary(self, response: str) -> PaperSummary:
        """Parse the AI response into structured summary."""
        lines = response.strip().split("\n")

        headline = ""
        takeaway = ""
        why_matters = ""
        key_takeaways = []
        tags = []
        
        # Temp buffers for takeaways
        current_takeaway = {}

        # Parse line by line
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("HEADLINE:"):
                headline = line.replace("HEADLINE:", "").strip()
            elif line.startswith("TAKEAWAY:"):
                takeaway = line.replace("TAKEAWAY:", "").strip()
            elif line.startswith("WHY_MATTERS:"):
                why_matters = line.replace("WHY_MATTERS:", "").strip()
            
            # Key Takeaways parsing (label + text)
            elif line.startswith("KEY_TAKEAWAY_1_LABEL:"):
                current_takeaway["label"] = line.replace("KEY_TAKEAWAY_1_LABEL:", "").strip()
            elif line.startswith("KEY_TAKEAWAY_1_TEXT:"):
                current_takeaway["text"] = line.replace("KEY_TAKEAWAY_1_TEXT:", "").strip()
                if "label" in current_takeaway and "text" in current_takeaway:
                    key_takeaways.append(f"**{current_takeaway['label']}**: {current_takeaway['text']}")
                    current_takeaway = {}
            
            elif line.startswith("KEY_TAKEAWAY_2_LABEL:"):
                current_takeaway["label"] = line.replace("KEY_TAKEAWAY_2_LABEL:", "").strip()
            elif line.startswith("KEY_TAKEAWAY_2_TEXT:"):
                current_takeaway["text"] = line.replace("KEY_TAKEAWAY_2_TEXT:", "").strip()
                if "label" in current_takeaway and "text" in current_takeaway:
                    key_takeaways.append(f"**{current_takeaway['label']}**: {current_takeaway['text']}")
                    current_takeaway = {}
                    
            elif line.startswith("KEY_TAKEAWAY_3_LABEL:"):
                current_takeaway["label"] = line.replace("KEY_TAKEAWAY_3_LABEL:", "").strip()
            elif line.startswith("KEY_TAKEAWAY_3_TEXT:"):
                current_takeaway["text"] = line.replace("KEY_TAKEAWAY_3_TEXT:", "").strip()
                if "label" in current_takeaway and "text" in current_takeaway:
                    key_takeaways.append(f"**{current_takeaway['label']}**: {current_takeaway['text']}")
                    current_takeaway = {}

            elif line.startswith("TAGS:"):
                tags_str = line.replace("TAGS:", "").strip()
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        # Fallback parsing for old format or AI hallucinations
        if not key_takeaways:
            for line in lines:
                if line.startswith("KEY_TAKEAWAY_1:"):
                    key_takeaways.append(line.replace("KEY_TAKEAWAY_1:", "").strip())
                elif line.startswith("KEY_TAKEAWAY_2:"):
                    key_takeaways.append(line.replace("KEY_TAKEAWAY_2:", "").strip())
                elif line.startswith("KEY_TAKEAWAY_3:"):
                    key_takeaways.append(line.replace("KEY_TAKEAWAY_3:", "").strip())

        # Ensure we have 3 takeaways
        while len(key_takeaways) < 3:
            key_takeaways.append("Use this knowledge to improve your understanding of the world.")

        return PaperSummary(
            headline=headline or "Research Finding",
            takeaway=takeaway or "Summary not available.",
            why_matters=why_matters or "Implications being assessed.",
            key_takeaways=key_takeaways[:3],
            tags=tags or ["research"],
        )
    
    def _set_field(self, field: str, text: List[str], context: dict):
        """Helper to set parsed field value."""
        value = " ".join(text)
        if field == "headline":
            context["headline"] = value
        elif field == "takeaway":
            context["takeaway"] = value
        elif field == "why_matters":
            context["why_matters"] = value
        elif field == "tags":
            context["tags"] = [t.strip() for t in value.split(",")]
    
    async def generate_digest_texts(
        self,
        papers: List[Paper],
        digest_name: str,
    ) -> tuple[str, str, str]:
        """Generate intro, connecting narrative, and conclusion for a digest."""

        # Get paper topics and headlines
        topics = []
        headlines = []
        for paper in papers:
            if paper.tags:
                topics.extend(paper.tags)
            if paper.summary_headline:
                headlines.append(paper.summary_headline)

        # Convert to list for slicing
        unique_topics = list(set(topics))[:10]
        topic_summary = ", ".join(unique_topics)

        # Create a summary of the papers for context
        papers_context = "\n".join([
            f"- {paper.summary_headline}: {paper.summary_takeaway[:200]}\n  Key Insight: {paper.key_takeaways[0] if paper.key_takeaways else ''}"
            for paper in papers if paper.summary_headline and paper.summary_takeaway
        ])

        intro_prompt = f"""Write an introduction for a science digest newsletter called "{digest_name}".

The digest covers {len(papers)} recent papers exploring: {topic_summary or "various scientific fields"}.

Papers included:
{papers_context}

FORMATTING RULES:
- Write 2 short paragraphs (3-4 sentences each)
- Use plain text only - NO markdown headers, NO bold, NO bullet points
- Start with a warm welcome that draws readers in
- Second paragraph previews the exciting findings ahead
- Keep it conversational and accessible
- End with anticipation for what's to come

The intro should feel like a friendly "Letter from the Editor" - warm, curious, and inviting."""

        narrative_prompt = f"""Write a connecting narrative for a science newsletter with {len(papers)} research papers.

Papers and their findings:
{papers_context}

FORMATTING RULES:
- Write 2-3 flowing paragraphs (total 200-300 words)
- Use plain text only - NO markdown headers, NO bold, NO bullet points, NO asterisks
- Each paragraph should flow naturally into the next
- Find the common threads and surprising connections between the papers
- Show how the findings complement or build upon each other
- Make it feel like a cohesive story, not a list

Write in an engaging, conversational style that weaves the research together."""

        conclusion_prompt = f"""Write a conclusion for this science digest newsletter.

The newsletter covered {len(papers)} papers on: {topic_summary or "various scientific fields"}

Key insights from the papers:
{papers_context}

Write EXACTLY in this format (no markdown, no asterisks, no ## headers):

THE BIG PICTURE

[1 paragraph synthesizing the main insights - what's the overarching lesson?]

Key Takeaways:
- [First essential insight from the research]
- [Second essential insight]
- [Third essential insight]

YOUR ACTION PLAN

This Week's Challenge:
[One specific, measurable action. Be concrete: "Write three things you're grateful for each morning"]

Quick Wins - Start Today:
- [First immediate action they can do now]
- [Second small habit tweak]
- [Third micro-experiment]

Your 30-Day Experiment:
[One habit to try this month. Specific: what to do, when, how to track.]

Discussion Starter:
[A thought-provoking question to discuss with others]

[End with 1-2 motivational sentences]

CRITICAL FORMATTING RULES:
- NO markdown: no ##, no **, no *, no bold markers
- Use plain text headers (just the words, no symbols)
- Use simple dashes (-) for bullets
- Keep it SHORT - this should fit in about 350 words total
- Be SPECIFIC with actions"""

        intro = await self.provider.complete(
            intro_prompt,
            system_prompt="You are a science communicator. NEVER use markdown: no *, no **, no ##, no italics. Write in plain text paragraphs only.",
            max_tokens=300,
        )

        narrative = await self.provider.complete(
            narrative_prompt,
            system_prompt="You are a science communicator. NEVER use markdown: no *, no **, no ##. Write in plain text paragraphs only.",
            max_tokens=400,
        )

        conclusion = await self.provider.complete(
            conclusion_prompt,
            system_prompt="You are a science communicator. NEVER use markdown symbols like ## or ** or *. Use plain text only. Follow the exact format in the prompt.",
            max_tokens=500,
        )

        return intro.strip(), narrative.strip(), conclusion.strip()
