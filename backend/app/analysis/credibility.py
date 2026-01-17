"""Credibility analysis engine."""
from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.paper import Paper
from app.models.app_settings import AppSettings
from app.ai.providers.base import get_ai_provider


class CredibilityAnalyzer:
    """Multi-factor credibility scoring system."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._weights = None
    
    async def _get_weights(self) -> dict:
        """Get credibility weights from settings."""
        if self._weights is None:
            result = await self.db.execute(
                select(AppSettings).where(AppSettings.id == 1)
            )
            settings = result.scalar_one_or_none()
            
            if settings:
                self._weights = {
                    "journal_impact": settings.journal_impact_weight,
                    "author_hindex": settings.author_hindex_weight,
                    "sample_size": settings.sample_size_weight,
                    "methodology": settings.methodology_weight,
                    "peer_review": settings.peer_review_weight,
                    "citation_velocity": settings.citation_velocity_weight,
                }
            else:
                # Default weights
                self._weights = {
                    "journal_impact": 0.25,
                    "author_hindex": 0.15,
                    "sample_size": 0.20,
                    "methodology": 0.20,
                    "peer_review": 0.10,
                    "citation_velocity": 0.10,
                }
        
        return self._weights
    
    async def analyze(self, paper: Paper) -> Tuple[float, dict, str]:
        """
        Analyze paper credibility.
        
        Returns:
            Tuple of (score, breakdown_dict, credibility_note)
        """
        weights = await self._get_weights()
        breakdown = {}
        
        # 1. Journal Impact Factor Score (0-100)
        journal_score = self._score_journal_impact(paper)
        breakdown["journal_impact"] = {
            "score": journal_score,
            "weight": weights["journal_impact"],
            "weighted_score": journal_score * weights["journal_impact"],
            "details": f"Impact factor: {paper.journal_impact_factor or 'Unknown'}"
        }
        
        # 2. Author H-Index Score (0-100)
        author_score = self._score_author_hindex(paper)
        breakdown["author_hindex"] = {
            "score": author_score,
            "weight": weights["author_hindex"],
            "weighted_score": author_score * weights["author_hindex"],
            "details": self._get_author_details(paper)
        }
        
        # 3. Sample Size Score (0-100)
        sample_score = await self._score_sample_size(paper)
        breakdown["sample_size"] = {
            "score": sample_score,
            "weight": weights["sample_size"],
            "weighted_score": sample_score * weights["sample_size"],
            "details": f"Sample size: {paper.sample_size or 'Not assessed'}"
        }
        
        # 4. Methodology Quality Score (0-100)
        method_score = await self._score_methodology(paper)
        breakdown["methodology"] = {
            "score": method_score,
            "weight": weights["methodology"],
            "weighted_score": method_score * weights["methodology"],
            "details": f"Study type: {paper.study_type or 'Not assessed'}"
        }
        
        # 5. Peer Review Status Score (0-100)
        review_score = self._score_peer_review(paper)
        breakdown["peer_review"] = {
            "score": review_score,
            "weight": weights["peer_review"],
            "weighted_score": review_score * weights["peer_review"],
            "details": "Peer-reviewed" if paper.is_peer_reviewed else "Preprint (not peer-reviewed)"
        }
        
        # 6. Citation Velocity Score (0-100)
        citation_score = self._score_citation_velocity(paper)
        breakdown["citation_velocity"] = {
            "score": citation_score,
            "weight": weights["citation_velocity"],
            "weighted_score": citation_score * weights["citation_velocity"],
            "details": f"Citations: {paper.citations or 0}"
        }
        
        # Calculate total score
        total_score = sum(b["weighted_score"] for b in breakdown.values())
        
        # Generate credibility note
        note = self._generate_credibility_note(total_score, breakdown, paper)
        
        return round(total_score, 1), breakdown, note
    
    def _score_journal_impact(self, paper: Paper) -> float:
        """Score based on journal impact factor."""
        if paper.journal_impact_factor is None:
            return 50.0  # Neutral score for unknown
        
        # Scale: 0-5 IF = 0-50, 5-20 IF = 50-80, 20+ IF = 80-100
        if paper.journal_impact_factor < 5:
            return (paper.journal_impact_factor / 5) * 50
        elif paper.journal_impact_factor < 20:
            return 50 + ((paper.journal_impact_factor - 5) / 15) * 30
        else:
            return min(100, 80 + ((paper.journal_impact_factor - 20) / 30) * 20)
    
    def _score_author_hindex(self, paper: Paper) -> float:
        """Score based on author h-index (uses max h-index among authors)."""
        if not paper.authors:
            return 50.0  # Neutral
        
        h_indices = [a.h_index for a in paper.authors if a.h_index is not None]
        if not h_indices:
            return 50.0
        
        max_h = max(h_indices)
        
        # Scale: h-index 0-10 = 0-40, 10-30 = 40-70, 30-60 = 70-90, 60+ = 90-100
        if max_h < 10:
            return (max_h / 10) * 40
        elif max_h < 30:
            return 40 + ((max_h - 10) / 20) * 30
        elif max_h < 60:
            return 70 + ((max_h - 30) / 30) * 20
        else:
            return min(100, 90 + ((max_h - 60) / 40) * 10)
    
    def _get_author_details(self, paper: Paper) -> str:
        """Get author h-index details."""
        if not paper.authors:
            return "No author information"
        
        h_indices = [(a.name, a.h_index) for a in paper.authors if a.h_index is not None]
        if not h_indices:
            return "Author h-indices not available"
        
        top_author = max(h_indices, key=lambda x: x[1])
        return f"Top author h-index: {top_author[1]} ({top_author[0]})"
    
    async def _score_sample_size(self, paper: Paper) -> float:
        """Score based on sample size (AI-extracted)."""
        if paper.sample_size is None:
            # Try to extract using AI
            paper.sample_size = await self._extract_sample_size(paper)
        
        if paper.sample_size is None:
            return 50.0  # Neutral
        
        # Scale varies by study type, use general scale
        # n < 30 = weak, 30-100 = moderate, 100-1000 = good, 1000+ = excellent
        n = paper.sample_size
        if n < 30:
            return 20 + (n / 30) * 20
        elif n < 100:
            return 40 + ((n - 30) / 70) * 20
        elif n < 1000:
            return 60 + ((n - 100) / 900) * 25
        else:
            return min(100, 85 + (min(n, 10000) - 1000) / 9000 * 15)
    
    async def _extract_sample_size(self, paper: Paper) -> Optional[int]:
        """Use AI to extract sample size from abstract."""
        if not paper.abstract:
            return None

        try:
            from app.core.config import settings
            provider = get_ai_provider(settings.default_ai_provider, settings.default_ai_model)
            
            prompt = f"""Extract the sample size (number of participants, subjects, or data points) from this abstract. 
Return ONLY a number, or "unknown" if not mentioned.

Abstract: {paper.abstract[:1500]}"""
            
            response = await provider.complete(prompt, max_tokens=20)
            
            # Try to parse number
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                return int(numbers[0])
        except:
            pass
        
        return None
    
    async def _score_methodology(self, paper: Paper) -> float:
        """Score based on methodology quality (AI-assessed)."""
        if paper.methodology_quality is None:
            paper.study_type, paper.methodology_quality = await self._assess_methodology(paper)
        
        quality_scores = {
            "meta_analysis": 95,
            "systematic_review": 90,
            "rct": 85,
            "cohort": 70,
            "case_control": 60,
            "cross_sectional": 50,
            "case_report": 30,
            "opinion": 20,
            "unknown": 50,
        }
        
        return quality_scores.get(paper.methodology_quality, 50)
    
    async def _assess_methodology(self, paper: Paper) -> Tuple[Optional[str], str]:
        """Use AI to assess study methodology."""
        if not paper.abstract:
            return None, "unknown"

        try:
            from app.core.config import settings
            provider = get_ai_provider(settings.default_ai_provider, settings.default_ai_model)
            
            prompt = f"""Classify this study's methodology. Choose ONE from:
- meta_analysis
- systematic_review  
- rct (randomized controlled trial)
- cohort
- case_control
- cross_sectional
- case_report
- opinion
- unknown

Abstract: {paper.abstract[:1500]}

Reply with ONLY the category name."""
            
            response = await provider.complete(prompt, max_tokens=20)
            methodology = response.strip().lower().replace(" ", "_")
            
            valid = ["meta_analysis", "systematic_review", "rct", "cohort", 
                     "case_control", "cross_sectional", "case_report", "opinion"]
            
            if methodology in valid:
                return methodology.replace("_", " ").title(), methodology
            
        except:
            pass
        
        return None, "unknown"
    
    def _score_peer_review(self, paper: Paper) -> float:
        """Score based on peer review status."""
        if paper.is_preprint:
            return 40.0  # Lower but not zero - preprints can be valuable
        return 100.0 if paper.is_peer_reviewed else 50.0
    
    def _score_citation_velocity(self, paper: Paper) -> float:
        """Score based on citations per month since publication."""
        if paper.citations is None or paper.published_date is None:
            return 50.0  # Neutral
        
        # Calculate months since publication
        now = datetime.utcnow()
        months = max(1, (now - paper.published_date).days / 30)
        
        velocity = paper.citations / months
        
        # Scale: 0-1 = poor, 1-5 = average, 5-20 = good, 20+ = excellent
        if velocity < 1:
            return 30 + velocity * 20
        elif velocity < 5:
            return 50 + ((velocity - 1) / 4) * 20
        elif velocity < 20:
            return 70 + ((velocity - 5) / 15) * 20
        else:
            return min(100, 90 + (min(velocity, 100) - 20) / 80 * 10)
    
    def _generate_credibility_note(
        self, 
        score: float, 
        breakdown: dict, 
        paper: Paper
    ) -> str:
        """Generate a basic credibility note (fallback for async context)."""
        # This is a synchronous fallback, the AI version is called separately
        if score >= 90:
            quality = "Excellent credibility"
        elif score >= 80:
            quality = "High credibility"
        elif score >= 60:
            quality = "Moderate credibility"
        elif score >= 40:
            quality = "Mixed credibility"
        else:
            quality = "Low credibility"
            
        return f"{quality} ({score:.0f}/100). Full AI assessment pending."
    
    async def generate_ai_credibility_note(
        self,
        paper: Paper,
        score: float,
        breakdown: dict,
        provider: str = "gemini",
        model: str = None
    ) -> str:
        """Generate an AI-powered credibility assessment."""
        from app.core.config import settings
        
        # Use configured provider
        actual_provider = provider or settings.default_ai_provider
        actual_model = model or settings.default_ai_model
        
        try:
            ai_provider = get_ai_provider(actual_provider, actual_model)
        except Exception:
            # Fallback to rule-based if AI unavailable
            return self._generate_credibility_note(score, breakdown, paper)
        
        # Build context for AI
        author_info = ", ".join([a.name for a in (paper.authors or [])[:3]]) or "Unknown authors"
        
        prompt = f"""You are a scientific credibility analyst. Assess this paper's trustworthiness in 2-3 sentences.

PAPER: {paper.title}
JOURNAL: {paper.journal or "Unknown"}
AUTHORS: {author_info}
PREPRINT: {"Yes (not peer-reviewed)" if paper.is_preprint else "No (peer-reviewed)"}
CITATIONS: {paper.citations or "Unknown"}

CREDIBILITY SCORES (out of 100):
- Overall: {score:.0f}/100
- Journal Impact: {breakdown['journal_impact']['score']:.0f}/100
- Author Experience: {breakdown['author_hindex']['score']:.0f}/100
- Sample Size: {breakdown['sample_size']['score']:.0f}/100
- Methodology: {breakdown['methodology']['score']:.0f}/100
- Peer Review: {breakdown['peer_review']['score']:.0f}/100
- Citation Velocity: {breakdown['citation_velocity']['score']:.0f}/100

ABSTRACT (first 500 chars): {(paper.abstract or "")[:500]}

Write a brief, balanced assessment (2-3 sentences) that:
1. States the overall credibility level
2. Highlights the strongest factor supporting credibility
3. Notes the main limitation or area for caution
4. Keeps a professional, neutral tone

Do NOT use bullet points. Write as flowing prose."""

        try:
            response = await ai_provider.complete(
                prompt,
                system_prompt="You are a scientific credibility analyst providing balanced, professional assessments. Be specific and evidence-based.",
                max_tokens=150,
                temperature=0.5,
            )
            return response.strip()
        except Exception as e:
            print(f"[Credibility] AI assessment failed: {e}")
            return self._generate_credibility_note(score, breakdown, paper)
