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
from app.services.domain_service import DomainService

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


# Domain/Branding endpoints

@router.get("/branding")
async def get_branding(db: AsyncSession = Depends(get_db)):
    """Get current domain branding configuration for frontend."""
    service = DomainService(db)
    return await service.get_branding()


@router.get("/domains")
async def list_domains(db: AsyncSession = Depends(get_db)):
    """List all available domains."""
    service = DomainService(db)
    domains = await service.list_domains()

    # Seed defaults if no domains exist
    if not domains:
        await service.seed_default_domains()
        domains = await service.list_domains()

    return {
        "domains": [d.to_branding_dict() for d in domains],
    }


@router.put("/domain/{domain_id}")
async def set_active_domain(domain_id: str, db: AsyncSession = Depends(get_db)):
    """Set the active domain."""
    service = DomainService(db)
    try:
        domain = await service.set_active_domain(domain_id)
        return domain.to_branding_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
