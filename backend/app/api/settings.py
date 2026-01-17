"""Settings and configuration API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.app_settings import AppSettings
from app.models.schemas import (
    SettingsResponse,
    SettingsUpdateRequest,
    CredibilityWeightsResponse,
    CredibilityWeightsUpdateRequest,
)

router = APIRouter()


@router.get("/", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get current application settings."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = AppSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return SettingsResponse.model_validate(settings)


@router.put("/", response_model=SettingsResponse)
async def update_settings(
    request: SettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update application settings."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)
    
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return SettingsResponse.model_validate(settings)


@router.get("/credibility-weights", response_model=CredibilityWeightsResponse)
async def get_credibility_weights(db: AsyncSession = Depends(get_db)):
    """Get credibility scoring weights."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return CredibilityWeightsResponse(
        journal_impact_weight=settings.journal_impact_weight,
        author_hindex_weight=settings.author_hindex_weight,
        sample_size_weight=settings.sample_size_weight,
        methodology_weight=settings.methodology_weight,
        peer_review_weight=settings.peer_review_weight,
        citation_velocity_weight=settings.citation_velocity_weight,
    )


@router.put("/credibility-weights", response_model=CredibilityWeightsResponse)
async def update_credibility_weights(
    request: CredibilityWeightsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update credibility scoring weights."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)
    
    # Update weights
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    
    # Normalize weights to sum to 1.0
    total = (
        settings.journal_impact_weight +
        settings.author_hindex_weight +
        settings.sample_size_weight +
        settings.methodology_weight +
        settings.peer_review_weight +
        settings.citation_velocity_weight
    )
    
    if total > 0:
        settings.journal_impact_weight /= total
        settings.author_hindex_weight /= total
        settings.sample_size_weight /= total
        settings.methodology_weight /= total
        settings.peer_review_weight /= total
        settings.citation_velocity_weight /= total
    
    await db.commit()
    await db.refresh(settings)
    
    return CredibilityWeightsResponse(
        journal_impact_weight=settings.journal_impact_weight,
        author_hindex_weight=settings.author_hindex_weight,
        sample_size_weight=settings.sample_size_weight,
        methodology_weight=settings.methodology_weight,
        peer_review_weight=settings.peer_review_weight,
        citation_velocity_weight=settings.citation_velocity_weight,
    )
