"""Topic clustering service for grouping related papers.

Uses AI to intelligently group papers into topic clusters and
select "Top N" stories for each domain.
"""
import json
import logging
from typing import List, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import get_ai_provider, AIProvider
from app.models.paper import Paper
from app.models.topic_cluster import TopicCluster
from app.models.domain_config import DomainConfig


logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    """Result of topic clustering."""
    name: str
    description: str
    keywords: List[str]
    paper_ids: List[int]
    importance_score: float
    is_top_pick: bool = False


class TopicClusterer:
    """AI-powered topic grouping for papers.

    Groups papers into logical topic clusters and identifies
    the most important/newsworthy stories.
    """

    CLUSTER_PROMPT = """You are a news editor organizing {count} articles into distinct topic groups.

ARTICLES:
{articles_json}

DOMAIN: {domain_name}
CONTEXT: {domain_context}

TASK: Group these articles into {max_clusters} distinct topics.

For each topic group, provide:
1. name: Short topic name (3-5 words, catchy headline style)
2. description: One sentence summary of what this topic covers
3. keywords: 3-5 keywords that define this topic
4. article_ids: List of article IDs that belong to this topic
5. importance_score: 0.0-1.0 based on newsworthiness (breaking news, major discoveries, trending topics get higher scores)

IMPORTANT:
- Each article should belong to exactly ONE topic
- Topics should be distinct and non-overlapping
- Sort topics by importance_score (most important first)
- Consider recency, source authority, and content significance

Respond with ONLY a JSON array of topic groups:
[
  {{
    "name": "Topic Name Here",
    "description": "Brief description of the topic",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "article_ids": [1, 2, 3],
    "importance_score": 0.85
  }},
  ...
]
"""

    TOP_PICKS_PROMPT = """You are selecting the {count} most important stories from these topic clusters for a {domain_name} digest.

CLUSTERS:
{clusters_json}

AVAILABLE ARTICLES:
{articles_json}

Select exactly {count} articles that should be highlighted as "Top Picks". Consider:
- Newsworthiness and impact
- Relevance to the {domain_name} domain
- Quality and credibility of source
- Timeliness (prefer recent news)
- Diversity (try to cover different topics)

Respond with ONLY a JSON object:
{{
  "top_pick_ids": [article_id1, article_id2, article_id3],
  "reasons": ["reason for pick 1", "reason for pick 2", "reason for pick 3"]
}}
"""

    def __init__(
        self,
        provider: str = "gemini",
        model: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """Initialize topic clusterer.

        Args:
            provider: AI provider name
            model: Specific model (optional)
            db: Database session for saving clusters
        """
        self.provider_name = provider
        self.model = model
        self.db = db
        self._provider: Optional[AIProvider] = None

    @property
    def provider(self) -> AIProvider:
        """Lazy load the AI provider."""
        if self._provider is None:
            self._provider = get_ai_provider(self.provider_name, self.model)
        return self._provider

    async def cluster(
        self,
        papers: List[Paper],
        max_clusters: int = 5,
        domain_config: Optional[DomainConfig] = None
    ) -> List[ClusterResult]:
        """Group papers into topic clusters.

        Args:
            papers: Papers to cluster
            max_clusters: Maximum number of clusters
            domain_config: Domain configuration for context

        Returns:
            List of ClusterResult objects
        """
        if not papers:
            return []

        # Build articles JSON for prompt
        articles = []
        for paper in papers:
            articles.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": (paper.abstract or "")[:500],  # Limit length
                "source": paper.source,
                "published": paper.published_date.isoformat() if paper.published_date else None,
                "triage_score": paper.triage_score,
            })

        # Build domain context
        domain_name = "general"
        domain_context = "General news and content"
        if domain_config:
            domain_name = domain_config.domain_id
            domain_context = f"{domain_config.ai_role}. Focus: {domain_config.content_focus}"

        # Build prompt
        prompt = self.CLUSTER_PROMPT.format(
            count=len(papers),
            articles_json=json.dumps(articles, indent=2),
            domain_name=domain_name,
            domain_context=domain_context,
            max_clusters=min(max_clusters, len(papers)),
        )

        try:
            response = await self.provider.complete(
                prompt=prompt,
                system_prompt="You are a news editor skilled at organizing content into logical topics.",
                max_tokens=2000,
                temperature=0.3,
            )

            return self._parse_cluster_response(response, papers)

        except Exception as e:
            logger.error(f"Topic clustering failed: {e}")
            # Fallback: put all papers in one cluster
            return [ClusterResult(
                name="All Articles",
                description="All articles in this digest",
                keywords=["news", "articles"],
                paper_ids=[p.id for p in papers],
                importance_score=0.5,
            )]

    async def pick_top_stories(
        self,
        clusters: List[ClusterResult],
        papers: List[Paper],
        count: int = 3,
        domain_config: Optional[DomainConfig] = None
    ) -> List[int]:
        """Select top N stories from clustered papers.

        Args:
            clusters: Clustered papers
            papers: All papers
            count: Number of top picks
            domain_config: Domain configuration

        Returns:
            List of paper IDs that are top picks
        """
        if not clusters or not papers:
            return []

        # Build data for prompt
        paper_map = {p.id: p for p in papers}
        clusters_json = [
            {
                "name": c.name,
                "description": c.description,
                "importance_score": c.importance_score,
                "article_ids": c.paper_ids,
            }
            for c in clusters
        ]

        articles_json = [
            {
                "id": p.id,
                "title": p.title,
                "source": p.source,
                "triage_score": p.triage_score,
            }
            for p in papers
        ]

        domain_name = domain_config.domain_id if domain_config else "general"

        prompt = self.TOP_PICKS_PROMPT.format(
            count=count,
            domain_name=domain_name,
            clusters_json=json.dumps(clusters_json, indent=2),
            articles_json=json.dumps(articles_json, indent=2),
        )

        try:
            response = await self.provider.complete(
                prompt=prompt,
                system_prompt="You are a news editor selecting the most important stories.",
                max_tokens=500,
                temperature=0.2,
            )

            return self._parse_top_picks_response(response, papers)

        except Exception as e:
            logger.error(f"Top picks selection failed: {e}")
            # Fallback: return first N papers sorted by triage score
            sorted_papers = sorted(
                papers,
                key=lambda p: p.triage_score or 0.5,
                reverse=True
            )
            return [p.id for p in sorted_papers[:count]]

    async def cluster_and_save(
        self,
        papers: List[Paper],
        digest_id: Optional[int] = None,
        domain_config: Optional[DomainConfig] = None,
        max_clusters: int = 5,
        top_picks_count: int = 3,
    ) -> List[TopicCluster]:
        """Cluster papers and save to database.

        Args:
            papers: Papers to cluster
            digest_id: Optional digest ID to associate with
            domain_config: Domain configuration
            max_clusters: Maximum clusters
            top_picks_count: Number of top picks

        Returns:
            List of saved TopicCluster objects
        """
        if not self.db:
            raise ValueError("Database session required for cluster_and_save")

        # Cluster papers
        cluster_results = await self.cluster(papers, max_clusters, domain_config)

        # Get top picks
        top_pick_ids = await self.pick_top_stories(
            cluster_results, papers, top_picks_count, domain_config
        )

        # Mark top pick clusters
        for cluster in cluster_results:
            if any(pid in top_pick_ids for pid in cluster.paper_ids):
                cluster.is_top_pick = True

        # Save to database
        paper_map = {p.id: p for p in papers}
        saved_clusters = []

        for i, result in enumerate(cluster_results):
            cluster = TopicCluster(
                digest_id=digest_id,
                domain_id=domain_config.domain_id if domain_config else None,
                name=result.name,
                description=result.description,
                keywords=",".join(result.keywords),
                order=i,
                is_top_pick=result.is_top_pick,
                paper_count=len(result.paper_ids),
                importance_score=result.importance_score,
            )

            # Add papers to cluster
            for pid in result.paper_ids:
                if pid in paper_map:
                    cluster.papers.append(paper_map[pid])

            self.db.add(cluster)
            saved_clusters.append(cluster)

        await self.db.commit()
        return saved_clusters

    def _parse_cluster_response(
        self,
        response: str,
        papers: List[Paper]
    ) -> List[ClusterResult]:
        """Parse AI response into ClusterResults."""
        try:
            # Clean response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            data = json.loads(cleaned)
            valid_ids = {p.id for p in papers}

            results = []
            for item in data:
                # Filter to only valid paper IDs
                paper_ids = [pid for pid in item.get("article_ids", []) if pid in valid_ids]
                if not paper_ids:
                    continue

                results.append(ClusterResult(
                    name=item.get("name", "Untitled Topic"),
                    description=item.get("description", ""),
                    keywords=item.get("keywords", []),
                    paper_ids=paper_ids,
                    importance_score=float(item.get("importance_score", 0.5)),
                ))

            # Sort by importance
            results.sort(key=lambda x: x.importance_score, reverse=True)
            return results

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse cluster response: {e}")
            # Fallback
            return [ClusterResult(
                name="All Articles",
                description="All articles",
                keywords=["news"],
                paper_ids=[p.id for p in papers],
                importance_score=0.5,
            )]

    def _parse_top_picks_response(
        self,
        response: str,
        papers: List[Paper]
    ) -> List[int]:
        """Parse AI response for top picks."""
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            data = json.loads(cleaned)
            valid_ids = {p.id for p in papers}

            return [pid for pid in data.get("top_pick_ids", []) if pid in valid_ids]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse top picks response: {e}")
            return []
