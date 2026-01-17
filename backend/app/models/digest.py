"""Digest database model."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class DigestStatus(str, enum.Enum):
    """Digest processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DigestPaper(Base):
    """Association table linking digests to papers with order."""
    __tablename__ = "digest_papers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("digests.id", ondelete="CASCADE"))
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    digest: Mapped["Digest"] = relationship(back_populates="digest_papers")
    paper: Mapped["Paper"] = relationship()


class Digest(Base):
    """Digest model representing a curated collection of paper summaries."""
    __tablename__ = "digests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    
    # Processing status
    status: Mapped[DigestStatus] = mapped_column(
        Enum(DigestStatus), 
        default=DigestStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI settings used
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o")
    summary_style: Mapped[str] = mapped_column(String(50), default="newsletter")
    
    # Generated content
    intro_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    connecting_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Links papers together
    conclusion_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Da Vinci style summary infographic
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    digest_papers: Mapped[List["DigestPaper"]] = relationship(
        back_populates="digest",
        cascade="all, delete-orphan",
        order_by="DigestPaper.order"
    )
    
    @property
    def papers(self):
        """Get papers in order."""
        return [dp.paper for dp in self.digest_papers]
    
    def __repr__(self):
        return f"<Digest(id={self.id}, name='{self.name}', status={self.status})>"
