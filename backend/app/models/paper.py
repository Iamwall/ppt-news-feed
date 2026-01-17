"""Paper database model."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Author(Base):
    """Author model."""
    __tablename__ = "authors"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    affiliation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    h_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    semantic_scholar_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"))
    paper: Mapped["Paper"] = relationship(back_populates="authors")


class Paper(Base):
    """Paper model representing a scientific publication."""
    __tablename__ = "papers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Basic metadata
    title: Mapped[str] = mapped_column(String(1000))
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Source information
    source: Mapped[str] = mapped_column(String(50))  # pubmed, arxiv, biorxiv, etc.
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ID in source system
    
    # Dates
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Citation metrics
    citations: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    influential_citations: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    altmetric_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Credibility scoring
    credibility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    credibility_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # AI-generated content
    summary_headline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary_takeaway: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_why_matters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_takeaways: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of 3 key takeaways
    credibility_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Generated image
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Journal metrics (for credibility)
    journal_impact_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_peer_reviewed: Mapped[bool] = mapped_column(default=True)
    is_preprint: Mapped[bool] = mapped_column(default=False)
    
    # Methodology info (AI extracted)
    study_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    methodology_quality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    authors: Mapped[List["Author"]] = relationship(
        back_populates="paper", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Paper(id={self.id}, title='{self.title[:50]}...')>"
