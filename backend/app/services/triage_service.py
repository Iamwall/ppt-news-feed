"""Triage service for AI-powered content filtering.

Uses a cheap/fast AI model (GPT-4o-mini, Claude Haiku, etc.) to quickly
evaluate incoming content before expensive main processing.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_ai_provider, AIProvider
from app.models.paper import Paper
from app.models.domain_config import DomainConfig


logger = logging.getLogger(__name__)


@dataclass
class TriageResult:
    """Result of triage evaluation."""
    paper_id: int
    is_actual_news: bool
    is_relevant: bool
    quality_score: float  # 0.0-1.0
    verdict: str  # "pass" or "reject"
    reason: str


class TriageService:
    """AI-powered content filtering service.

    Uses a fast, cheap model to pre-filter content before main processing.
    This reduces noise and saves costs on expensive summarization.
    """

    # Default to fast/cheap models
    DEFAULT_PROVIDERS = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "gemini": "gemini-1.5-flash",
        "groq": "llama-3.1-8b-instant",
    }

    TRIAGE_PROMPT = """You are a content triage agent. Evaluate this article quickly and objectively.

Title: {title}
Source: {source}
Abstract/Content: {abstract}

Domain Context: {domain_context}

Evaluate and respond with ONLY a JSON object (no markdown, no explanation):
{{
    "is_actual_news": true/false,
    "is_relevant": true/false,
    "quality_score": 0.0-1.0,
    "verdict": "pass" or "reject",
    "reason": "brief explanation (max 50 words)"
}}

Criteria:
- is_actual_news: Is this real news/research content? (not ads, clickbait, spam, promotional content)
- is_relevant: Is this relevant to the {domain_name} domain?
- quality_score: Rate content quality (0.0 = spam, 1.0 = high quality original content)
- verdict: "pass" if is_actual_news AND is_relevant AND quality_score >= 0.3, else "reject"
"""

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """Initialize triage service.

        Args:
            provider: AI provider name (openai, anthropic, gemini, groq)
            model: Specific model override (defaults to fast/cheap model for provider)
            db: Database session for updating papers
        """
        self.provider_name = provider
        self.model = model or self.DEFAULT_PROVIDERS.get(provider, "gpt-4o-mini")
        self.db = db
        self._provider: Optional[AIProvider] = None

    @property
    def provider(self) -> AIProvider:
        """Lazy load the AI provider."""
        if self._provider is None:
            self._provider = get_ai_provider(self.provider_name, self.model)
        return self._provider

    async def triage_paper(
        self,
        paper: Paper,
        domain_config: Optional[DomainConfig] = None
    ) -> TriageResult:
        """Evaluate a single paper through triage.

        Args:
            paper: Paper to evaluate
            domain_config: Domain configuration for context

        Returns:
            TriageResult with evaluation
        """
        # Build domain context
        domain_name = "general"
        domain_context = "General news and content"

        if domain_config:
            domain_name = domain_config.domain_id
            domain_context = f"{domain_config.ai_role}. Focus: {domain_config.content_focus}"

        # Build prompt
        prompt = self.TRIAGE_PROMPT.format(
            title=paper.title or "Unknown",
            source=paper.source or "Unknown",
            abstract=(paper.abstract or "No content available")[:1000],  # Limit to 1000 chars
            domain_context=domain_context,
            domain_name=domain_name,
        )

        try:
            # Call AI for evaluation
            response = await self.provider.complete(
                prompt=prompt,
                system_prompt="You are a fast content triage agent. Respond only with valid JSON.",
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent decisions
            )

            # Parse response
            result = self._parse_response(response, paper.id)

            # Update paper if we have a db session
            if self.db:
                await self._update_paper(paper, result)

            return result

        except Exception as e:
            logger.error(f"Triage failed for paper {paper.id}: {e}")
            # On error, default to passing the content (fail-open for backward compatibility)
            return TriageResult(
                paper_id=paper.id,
                is_actual_news=True,
                is_relevant=True,
                quality_score=0.5,
                verdict="pass",
                reason=f"Triage error (auto-passed): {str(e)[:50]}"
            )

    async def triage_batch(
        self,
        papers: List[Paper],
        domain_config: Optional[DomainConfig] = None,
        skip_triaged: bool = True
    ) -> List[TriageResult]:
        """Evaluate multiple papers through triage.

        Args:
            papers: List of papers to evaluate
            domain_config: Domain configuration for context
            skip_triaged: Skip papers already triaged (default True)

        Returns:
            List of TriageResults
        """
        results = []

        for paper in papers:
            # Skip already triaged papers if requested
            if skip_triaged and paper.triage_status and paper.triage_status != "pending":
                logger.debug(f"Skipping already triaged paper {paper.id}")
                results.append(TriageResult(
                    paper_id=paper.id,
                    is_actual_news=paper.triage_status == "passed",
                    is_relevant=paper.triage_status == "passed",
                    quality_score=paper.triage_score or 0.5,
                    verdict=paper.triage_status,
                    reason=paper.triage_reason or "Previously triaged"
                ))
                continue

            result = await self.triage_paper(paper, domain_config)
            results.append(result)

        return results

    def _parse_response(self, response: str, paper_id: int) -> TriageResult:
        """Parse AI response into TriageResult."""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            data = json.loads(cleaned)

            return TriageResult(
                paper_id=paper_id,
                is_actual_news=bool(data.get("is_actual_news", True)),
                is_relevant=bool(data.get("is_relevant", True)),
                quality_score=float(data.get("quality_score", 0.5)),
                verdict=str(data.get("verdict", "pass")).lower(),
                reason=str(data.get("reason", ""))[:200],
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse triage response: {e}")
            # Default to passing on parse error (backward compatible)
            return TriageResult(
                paper_id=paper_id,
                is_actual_news=True,
                is_relevant=True,
                quality_score=0.5,
                verdict="pass",
                reason=f"Parse error (auto-passed): {str(e)[:50]}"
            )

    async def _update_paper(self, paper: Paper, result: TriageResult) -> None:
        """Update paper with triage results."""
        paper.triage_status = "passed" if result.verdict == "pass" else "rejected"
        paper.triage_score = result.quality_score
        paper.triage_reason = result.reason
        paper.triage_model = f"{self.provider_name}/{self.model}"
        paper.triaged_at = datetime.utcnow()

        if self.db:
            self.db.add(paper)
            await self.db.commit()


async def run_triage_on_papers(
    db: AsyncSession,
    papers: List[Paper],
    domain_config: Optional[DomainConfig] = None,
    provider: str = "openai",
    model: Optional[str] = None,
) -> dict:
    """Convenience function to run triage on a list of papers.

    Args:
        db: Database session
        papers: Papers to triage
        domain_config: Domain configuration
        provider: AI provider name
        model: Specific model (optional)

    Returns:
        Dict with stats: {"total", "passed", "rejected", "results"}
    """
    service = TriageService(provider=provider, model=model, db=db)
    results = await service.triage_batch(papers, domain_config)

    passed = [r for r in results if r.verdict == "pass"]
    rejected = [r for r in results if r.verdict == "reject"]

    return {
        "total": len(results),
        "passed": len(passed),
        "rejected": len(rejected),
        "pass_rate": len(passed) / len(results) if results else 0,
        "results": results,
    }
