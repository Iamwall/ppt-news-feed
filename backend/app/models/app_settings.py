"""Application settings database model."""
from typing import Optional, List
from sqlalchemy import String, Float, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AppSettings(Base):
    """Persistent application settings."""
    __tablename__ = "app_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # AI Provider settings
    default_ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    default_ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o")
    default_summary_style: Mapped[str] = mapped_column(String(50), default="newsletter")
    
    # Image generation
    default_image_provider: Mapped[str] = mapped_column(String(50), default="gemini")
    generate_images_by_default: Mapped[bool] = mapped_column(Boolean, default=True)
    image_style: Mapped[str] = mapped_column(String(100), default="scientific_illustration")
    
    # Credibility weights (should sum to 1.0)
    journal_impact_weight: Mapped[float] = mapped_column(Float, default=0.25)
    author_hindex_weight: Mapped[float] = mapped_column(Float, default=0.15)
    sample_size_weight: Mapped[float] = mapped_column(Float, default=0.20)
    methodology_weight: Mapped[float] = mapped_column(Float, default=0.20)
    peer_review_weight: Mapped[float] = mapped_column(Float, default=0.10)
    citation_velocity_weight: Mapped[float] = mapped_column(Float, default=0.10)
    
    # Fetch settings
    enabled_sources: Mapped[list] = mapped_column(JSON, default=list)
    default_keywords: Mapped[list] = mapped_column(JSON, default=list)
    default_max_results: Mapped[int] = mapped_column(Integer, default=50)
    default_days_back: Mapped[int] = mapped_column(Integer, default=7)
    
    # Email settings
    email_template: Mapped[str] = mapped_column(String(100), default="default")
    include_images_in_email: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Scheduling
    auto_fetch_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_fetch_cron: Mapped[str] = mapped_column(String(100), default="0 8 * * 1")  # Weekly Monday 8am
    
    def __repr__(self):
        return f"<AppSettings(id={self.id})>"
