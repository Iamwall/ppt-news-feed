"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# Enums
class DigestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FetchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SummaryStyle(str, Enum):
    NEWSLETTER = "newsletter"
    TECHNICAL = "technical"
    LAYPERSON = "layperson"


# Author schemas
class AuthorBase(BaseModel):
    name: str
    affiliation: Optional[str] = None
    h_index: Optional[int] = None


class AuthorResponse(AuthorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Paper schemas
class PaperBase(BaseModel):
    title: str
    abstract: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str


class PaperResponse(PaperBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    source_id: Optional[str] = None
    published_date: Optional[datetime] = None
    fetched_at: datetime
    
    # Metrics
    citations: Optional[int] = None
    influential_citations: Optional[int] = None
    altmetric_score: Optional[float] = None
    
    # Credibility
    credibility_score: Optional[float] = None
    credibility_breakdown: Optional[dict] = None
    
    # Summaries
    summary_headline: Optional[str] = None
    summary_takeaway: Optional[str] = None
    summary_why_matters: Optional[str] = None
    key_takeaways: Optional[List[str]] = None
    credibility_note: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Image
    image_path: Optional[str] = None
    
    # Methodology
    study_type: Optional[str] = None
    sample_size: Optional[int] = None
    methodology_quality: Optional[str] = None
    is_preprint: bool = False
    
    authors: List[AuthorResponse] = []


class PaperListResponse(BaseModel):
    papers: List[PaperResponse]
    total: int
    skip: int
    limit: int


# Digest schemas
class DigestCreateRequest(BaseModel):
    name: str
    paper_ids: List[int]
    ai_provider: str = "gemini"
    ai_model: str = "gemini-2.0-flash-exp"
    summary_style: SummaryStyle = SummaryStyle.NEWSLETTER
    generate_images: bool = True


class DigestPaperResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    paper: PaperResponse
    order: int


class DigestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    status: DigestStatus
    error_message: Optional[str] = None
    ai_provider: str
    ai_model: str
    summary_style: str
    intro_text: Optional[str] = None
    connecting_narrative: Optional[str] = None
    conclusion_text: Optional[str] = None
    summary_image_path: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    digest_papers: List[DigestPaperResponse] = []


class DigestListResponse(BaseModel):
    digests: List[DigestResponse]
    total: int
    skip: int
    limit: int


# Fetch schemas
class FetchRequest(BaseModel):
    sources: List[str] = Field(
        default=["pubmed", "arxiv"],
        description="Sources to fetch from"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to search for"
    )
    max_results: int = Field(default=50, ge=1, le=500)
    days_back: int = Field(default=7, ge=1, le=365)
    # Triage options (optional, backward compatible)
    enable_triage: bool = Field(
        default=False,
        description="Run AI triage to filter noise before saving"
    )
    triage_provider: Optional[str] = Field(
        default="openai",
        description="AI provider for triage (openai, anthropic, gemini, groq)"
    )
    triage_model: Optional[str] = Field(
        default=None,
        description="Specific model for triage (defaults to fast/cheap model)"
    )


class FetchResponse(BaseModel):
    job_id: int
    status: FetchStatus
    message: str


class FetchStatusResponse(BaseModel):
    job_id: int
    status: FetchStatus
    progress: int
    current_source: Optional[str] = None
    papers_fetched: int
    papers_new: int
    papers_updated: int
    errors: Optional[List[str]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# Newsletter schemas
class NewsletterExportRequest(BaseModel):
    format: Literal["html", "pdf", "markdown"] = "html"


# Settings schemas
class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    default_ai_provider: str
    default_ai_model: str
    default_summary_style: str
    default_image_provider: str
    generate_images_by_default: bool
    image_style: str
    enabled_sources: List[str]
    default_keywords: List[str]
    default_max_results: int
    default_days_back: int
    email_template: str
    include_images_in_email: bool
    auto_fetch_enabled: bool
    auto_fetch_cron: str


class SettingsUpdateRequest(BaseModel):
    default_ai_provider: Optional[str] = None
    default_ai_model: Optional[str] = None
    default_summary_style: Optional[str] = None
    default_image_provider: Optional[str] = None
    generate_images_by_default: Optional[bool] = None
    image_style: Optional[str] = None
    enabled_sources: Optional[List[str]] = None
    default_keywords: Optional[List[str]] = None
    default_max_results: Optional[int] = None
    default_days_back: Optional[int] = None
    email_template: Optional[str] = None
    include_images_in_email: Optional[bool] = None
    auto_fetch_enabled: Optional[bool] = None
    auto_fetch_cron: Optional[str] = None


class CredibilityWeightsResponse(BaseModel):
    journal_impact_weight: float
    author_hindex_weight: float
    sample_size_weight: float
    methodology_weight: float
    peer_review_weight: float
    citation_velocity_weight: float


class CredibilityWeightsUpdateRequest(BaseModel):
    journal_impact_weight: Optional[float] = Field(None, ge=0, le=1)
    author_hindex_weight: Optional[float] = Field(None, ge=0, le=1)
    sample_size_weight: Optional[float] = Field(None, ge=0, le=1)
    methodology_weight: Optional[float] = Field(None, ge=0, le=1)
    peer_review_weight: Optional[float] = Field(None, ge=0, le=1)
    citation_velocity_weight: Optional[float] = Field(None, ge=0, le=1)
