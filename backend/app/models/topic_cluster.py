"""Topic cluster model for grouping related papers."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Float, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Association table for many-to-many relationship between clusters and papers
cluster_papers = Table(
    "cluster_papers",
    Base.metadata,
    Column("cluster_id", Integer, ForeignKey("topic_clusters.id", ondelete="CASCADE"), primary_key=True),
    Column("paper_id", Integer, ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True),
    Column("relevance_score", Float, default=1.0),  # How relevant paper is to this topic
    Column("order", Integer, default=0),  # Display order within cluster
)


class TopicCluster(Base):
    """Groups related papers by topic.

    Used by Daily Digest mode to organize papers into logical topic groups
    for easier consumption. AI determines groupings and picks "Top N" stories.
    """
    __tablename__ = "topic_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Parent digest (optional - clusters can exist without digest)
    digest_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("digests.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Domain association
    domain_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Cluster identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # AI-generated topic name
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Topic summary
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated keywords

    # Display settings
    order: Mapped[int] = mapped_column(Integer, default=0)  # Display order within digest
    is_top_pick: Mapped[bool] = mapped_column(Boolean, default=False)  # Highlighted cluster
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Optional icon name

    # Metrics
    paper_count: Mapped[int] = mapped_column(Integer, default=0)
    importance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0-1.0 newsworthiness
    avg_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Avg paper quality

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    papers: Mapped[List["Paper"]] = relationship(
        secondary=cluster_papers,
        backref="topic_clusters"
    )

    def __repr__(self):
        return f"<TopicCluster(id={self.id}, name='{self.name}', papers={self.paper_count})>"


# Import here to avoid circular import
from app.models.paper import Paper
