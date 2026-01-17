"""Domain configuration service."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_config import DomainConfig, DEFAULT_DOMAINS
from app.models.app_settings import AppSettings


class DomainService:
    """Service for managing domain configurations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_domain(self) -> DomainConfig:
        """Get the currently active domain configuration."""
        # Get the active domain ID from settings
        settings = await self._get_or_create_settings()
        domain_id = settings.active_domain_id or "science"

        # Get the domain config
        domain = await self.get_domain_by_id(domain_id)
        if not domain:
            # Fallback to science domain or create it
            domain = await self.get_domain_by_id("science")
            if not domain:
                await self.seed_default_domains()
                domain = await self.get_domain_by_id("science")

        return domain

    async def get_domain_by_id(self, domain_id: str) -> Optional[DomainConfig]:
        """Get a domain configuration by ID."""
        result = await self.db.execute(
            select(DomainConfig).where(DomainConfig.domain_id == domain_id)
        )
        return result.scalar_one_or_none()

    async def list_domains(self) -> list[DomainConfig]:
        """List all available domain configurations."""
        result = await self.db.execute(
            select(DomainConfig).where(DomainConfig.is_active == True).order_by(DomainConfig.domain_id)
        )
        return list(result.scalars().all())

    async def set_active_domain(self, domain_id: str) -> DomainConfig:
        """Set the active domain."""
        # Verify domain exists
        domain = await self.get_domain_by_id(domain_id)
        if not domain:
            raise ValueError(f"Domain '{domain_id}' not found")

        # Update settings
        settings = await self._get_or_create_settings()
        settings.active_domain_id = domain_id
        await self.db.commit()

        return domain

    async def get_branding(self) -> dict:
        """Get branding info for frontend."""
        domain = await self.get_active_domain()
        return domain.to_branding_dict()

    async def seed_default_domains(self) -> None:
        """Seed the database with default domain configurations."""
        for domain_data in DEFAULT_DOMAINS:
            existing = await self.get_domain_by_id(domain_data["domain_id"])
            if not existing:
                domain = DomainConfig(**domain_data)
                self.db.add(domain)

        await self.db.commit()

    async def _get_or_create_settings(self) -> AppSettings:
        """Get or create application settings."""
        result = await self.db.execute(select(AppSettings))
        settings = result.scalar_one_or_none()

        if not settings:
            settings = AppSettings()
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings


async def get_domain_service(db: AsyncSession) -> DomainService:
    """Dependency for getting domain service."""
    return DomainService(db)
