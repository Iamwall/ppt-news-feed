"""Fetch job database model."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class FetchStatus(str, enum.Enum):
    """Fetch job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FetchJob(Base):
    """Tracks paper fetch operations."""
    __tablename__ = "fetch_jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Job configuration
    sources: Mapped[list] = mapped_column(JSON)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    max_results: Mapped[int] = mapped_column(Integer, default=50)
    days_back: Mapped[int] = mapped_column(Integer, default=7)
    
    # Status
    status: Mapped[FetchStatus] = mapped_column(
        Enum(FetchStatus),
        default=FetchStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)  # Percentage
    current_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Results
    papers_fetched: Mapped[int] = mapped_column(Integer, default=0)
    papers_new: Mapped[int] = mapped_column(Integer, default=0)
    papers_updated: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<FetchJob(id={self.id}, status={self.status})>"
