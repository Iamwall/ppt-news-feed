"""Domain configuration model for multi-domain support."""
from typing import Optional
from sqlalchemy import String, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DomainConfig(Base):
    """Domain-specific configuration for branding and behavior."""
    __tablename__ = "domain_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Branding
    app_name: Mapped[str] = mapped_column(String(100), default="News Digest")
    tagline: Mapped[str] = mapped_column(String(200), default="Content Aggregator")
    newsletter_title: Mapped[str] = mapped_column(String(200), default="Newsletter")
    footer_text: Mapped[str] = mapped_column(String(200), default="Stay informed!")

    # Colors (hex codes)
    primary_color: Mapped[str] = mapped_column(String(20), default="#14b8aa")
    secondary_color: Mapped[str] = mapped_column(String(20), default="#0d948b")
    accent_color: Mapped[str] = mapped_column(String(20), default="#f59e0b")

    # Icon (Lucide icon name)
    icon_name: Mapped[str] = mapped_column(String(50), default="Newspaper")

    # Content terminology
    item_singular: Mapped[str] = mapped_column(String(50), default="article")
    item_plural: Mapped[str] = mapped_column(String(50), default="articles")
    source_label: Mapped[str] = mapped_column(String(50), default="source")

    # AI context for prompts
    ai_role: Mapped[str] = mapped_column(String(100), default="content analyst")
    content_focus: Mapped[str] = mapped_column(String(200), default="news and information")

    # Credibility factors (JSON dict with factor_name: weight)
    credibility_factors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Enabled built-in sources (JSON list of source IDs)
    enabled_sources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Description for UI
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<DomainConfig(domain_id={self.domain_id}, app_name={self.app_name})>"

    def to_branding_dict(self) -> dict:
        """Return branding info for frontend."""
        return {
            "domainId": self.domain_id,
            "appName": self.app_name,
            "tagline": self.tagline,
            "newsletterTitle": self.newsletter_title,
            "footerText": self.footer_text,
            "primaryColor": self.primary_color,
            "secondaryColor": self.secondary_color,
            "accentColor": self.accent_color,
            "iconName": self.icon_name,
            "itemSingular": self.item_singular,
            "itemPlural": self.item_plural,
            "sourceLabel": self.source_label,
            "aiRole": self.ai_role,
            "contentFocus": self.content_focus,
            "description": self.description,
        }


# Default domain configurations to seed
DEFAULT_DOMAINS = [
    {
        "domain_id": "science",
        "is_default": True,
        "app_name": "Science Digest",
        "tagline": "Research Aggregator",
        "newsletter_title": "Science Digest Newsletter",
        "footer_text": "Stay curious!",
        "primary_color": "#14b8aa",
        "secondary_color": "#0d948b",
        "accent_color": "#6366f1",
        "icon_name": "FlaskConical",
        "item_singular": "paper",
        "item_plural": "papers",
        "source_label": "database",
        "ai_role": "science communicator",
        "content_focus": "scientific research",
        "description": "Aggregate and summarize scientific research papers",
        "enabled_sources": ["pubmed", "arxiv", "biorxiv", "medrxiv", "semantic_scholar", "plos", "nature_rss", "science_rss", "lancet_rss", "nejm_rss", "bmj_rss"],
        "credibility_factors": {
            "journal_impact": 0.25,
            "author_hindex": 0.15,
            "sample_size": 0.20,
            "methodology": 0.20,
            "peer_review": 0.10,
            "citation_velocity": 0.10,
        },
    },
    {
        "domain_id": "tech",
        "app_name": "Tech Pulse",
        "tagline": "Innovation Tracker",
        "newsletter_title": "Tech Pulse Weekly",
        "footer_text": "Stay ahead of the curve!",
        "primary_color": "#3b82f6",
        "secondary_color": "#2563eb",
        "accent_color": "#8b5cf6",
        "icon_name": "Cpu",
        "item_singular": "article",
        "item_plural": "articles",
        "source_label": "feed",
        "ai_role": "technology analyst",
        "content_focus": "technology news and innovations",
        "description": "Track technology trends and innovations",
        "enabled_sources": ["arxiv"],
        "credibility_factors": {
            "source_reputation": 0.30,
            "author_expertise": 0.20,
            "verification": 0.25,
            "recency": 0.15,
            "engagement": 0.10,
        },
    },
    {
        "domain_id": "business",
        "app_name": "Business Brief",
        "tagline": "Market Intelligence",
        "newsletter_title": "Business Brief Weekly",
        "footer_text": "Stay profitable!",
        "primary_color": "#10b981",
        "secondary_color": "#059669",
        "accent_color": "#f59e0b",
        "icon_name": "Briefcase",
        "item_singular": "report",
        "item_plural": "reports",
        "source_label": "outlet",
        "ai_role": "business analyst",
        "content_focus": "business news and market trends",
        "description": "Aggregate business and financial news",
        "enabled_sources": [],
        "credibility_factors": {
            "source_tier": 0.30,
            "analyst_rating": 0.20,
            "data_backed": 0.25,
            "regulatory_filing": 0.15,
            "market_impact": 0.10,
        },
    },
    {
        "domain_id": "health",
        "app_name": "Health Insights",
        "tagline": "Wellness Knowledge",
        "newsletter_title": "Health Insights Weekly",
        "footer_text": "Stay healthy!",
        "primary_color": "#ec4899",
        "secondary_color": "#db2777",
        "accent_color": "#14b8a6",
        "icon_name": "Heart",
        "item_singular": "article",
        "item_plural": "articles",
        "source_label": "source",
        "ai_role": "health communicator",
        "content_focus": "health and wellness information",
        "description": "Health and medical news for general audiences",
        "enabled_sources": ["pubmed", "nejm_rss", "lancet_rss", "bmj_rss", "medrxiv"],
        "credibility_factors": {
            "journal_impact": 0.25,
            "clinical_evidence": 0.25,
            "peer_review": 0.20,
            "author_credentials": 0.15,
            "recency": 0.15,
        },
    },
    {
        "domain_id": "news",
        "app_name": "Daily Digest",
        "tagline": "News Aggregator",
        "newsletter_title": "Daily Digest",
        "footer_text": "Stay informed!",
        "primary_color": "#f59e0b",
        "secondary_color": "#d97706",
        "accent_color": "#3b82f6",
        "icon_name": "Newspaper",
        "item_singular": "story",
        "item_plural": "stories",
        "source_label": "outlet",
        "ai_role": "news editor",
        "content_focus": "current events and news",
        "description": "General news aggregation and summarization",
        "enabled_sources": [],
        "credibility_factors": {
            "source_reputation": 0.35,
            "fact_check_status": 0.25,
            "corroboration": 0.20,
            "recency": 0.10,
            "transparency": 0.10,
        },
    },
]
