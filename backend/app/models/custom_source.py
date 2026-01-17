"""Custom source model for user-defined RSS feeds."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Float, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class CustomSource(Base):
    """User-defined RSS feed or custom source."""
    __tablename__ = "custom_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(50), index=True)

    # Source identification
    name: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(50), default="rss")  # rss, atom, api

    # Connection
    url: Mapped[str] = mapped_column(Text)

    # Configuration (JSON for parser options, auth, etc.)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Credibility
    credibility_base_score: Mapped[float] = mapped_column(Float, default=50.0)
    is_peer_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Tracking
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetch_count: Mapped[int] = mapped_column(default=0)

    def __repr__(self):
        return f"<CustomSource(name={self.name}, domain={self.domain_id})>"

    def to_dict(self) -> dict:
        """Return source info for API response."""
        return {
            "id": self.id,
            "domainId": self.domain_id,
            "name": self.name,
            "sourceId": self.source_id,
            "sourceType": self.source_type,
            "url": self.url,
            "description": self.description,
            "isActive": self.is_active,
            "credibilityBaseScore": self.credibility_base_score,
            "isPeerReviewed": self.is_peer_reviewed,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastFetchedAt": self.last_fetched_at.isoformat() if self.last_fetched_at else None,
            "lastError": self.last_error,
            "fetchCount": self.fetch_count,
            "isCustom": True,
        }
