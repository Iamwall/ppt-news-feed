"""Digest schedule API endpoints."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.digest_schedule import DigestSchedule, ScheduledDigest
from app.services.scheduler_service import digest_scheduler


router = APIRouter()


# Pydantic schemas
class DigestScheduleCreate(BaseModel):
    """Schema for creating a digest schedule."""
    domain_id: str = Field(..., description="Domain ID for this schedule")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 6 * * *' for 6 AM daily)")
    timezone: str = Field(default="UTC")
    is_active: bool = Field(default=True)

    # Generation settings
    lookback_hours: int = Field(default=24, ge=1, le=168)  # Max 1 week
    max_items: int = Field(default=10, ge=1, le=50)
    top_picks_count: int = Field(default=3, ge=1, le=10)
    cluster_topics: bool = Field(default=True)

    # Filter settings
    min_triage_score: Optional[float] = Field(default=0.3, ge=0.0, le=1.0)
    only_passed_triage: bool = Field(default=True)

    # AI settings
    ai_provider: str = Field(default="gemini")
    ai_model: Optional[str] = None


class DigestScheduleUpdate(BaseModel):
    """Schema for updating a digest schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    lookback_hours: Optional[int] = Field(None, ge=1, le=168)
    max_items: Optional[int] = Field(None, ge=1, le=50)
    top_picks_count: Optional[int] = Field(None, ge=1, le=10)
    cluster_topics: Optional[bool] = None
    min_triage_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    only_passed_triage: Optional[bool] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None


class DigestScheduleResponse(BaseModel):
    """Response schema for a digest schedule."""
    id: int
    domain_id: str
    name: str
    description: Optional[str]
    cron_expression: str
    timezone: str
    is_active: bool
    lookback_hours: int
    max_items: int
    top_picks_count: int
    cluster_topics: bool
    min_triage_score: Optional[float]
    only_passed_triage: bool
    ai_provider: str
    ai_model: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    run_count: int
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledDigestResponse(BaseModel):
    """Response schema for a scheduled digest record."""
    id: int
    schedule_id: int
    digest_id: int
    papers_considered: int
    papers_included: int
    topics_clustered: int
    triggered_at: datetime
    completed_at: Optional[datetime]
    generation_time_seconds: Optional[float]

    class Config:
        from_attributes = True


# Endpoints
@router.get("/", response_model=List[DigestScheduleResponse])
async def list_schedules(
    domain_id: Optional[str] = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all digest schedules.

    Args:
        domain_id: Filter by domain (optional)
        active_only: Only return active schedules
    """
    query = select(DigestSchedule)

    if domain_id:
        query = query.where(DigestSchedule.domain_id == domain_id)

    if active_only:
        query = query.where(DigestSchedule.is_active == True)

    query = query.order_by(DigestSchedule.created_at.desc())

    result = await db.execute(query)
    schedules = result.scalars().all()

    return schedules


@router.get("/{schedule_id}", response_model=DigestScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific digest schedule."""
    result = await db.execute(
        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return schedule


@router.post("/", response_model=DigestScheduleResponse)
async def create_schedule(
    data: DigestScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new digest schedule.

    The schedule will automatically start generating digests
    according to the cron expression.
    """
    # Validate cron expression (basic check)
    cron_parts = data.cron_expression.split()
    if len(cron_parts) != 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Must have 5 parts: minute hour day month day_of_week"
        )

    schedule = DigestSchedule(
        domain_id=data.domain_id,
        name=data.name,
        description=data.description,
        cron_expression=data.cron_expression,
        timezone=data.timezone,
        is_active=data.is_active,
        lookback_hours=data.lookback_hours,
        max_items=data.max_items,
        top_picks_count=data.top_picks_count,
        cluster_topics=data.cluster_topics,
        min_triage_score=data.min_triage_score,
        only_passed_triage=data.only_passed_triage,
        ai_provider=data.ai_provider,
        ai_model=data.ai_model,
    )

    await digest_scheduler.add_schedule(db, schedule)

    return schedule


@router.put("/{schedule_id}", response_model=DigestScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: DigestScheduleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a digest schedule."""
    result = await db.execute(
        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Validate cron expression if provided
    if data.cron_expression:
        cron_parts = data.cron_expression.split()
        if len(cron_parts) != 5:
            raise HTTPException(
                status_code=400,
                detail="Invalid cron expression. Must have 5 parts."
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    schedule.updated_at = datetime.utcnow()

    await digest_scheduler.update_schedule(db, schedule)

    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a digest schedule."""
    result = await db.execute(
        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await digest_scheduler.delete_schedule(db, schedule_id)

    return {"message": "Schedule deleted", "id": schedule_id}


@router.post("/{schedule_id}/run-now")
async def trigger_schedule_now(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger a schedule to run immediately.

    This creates a new digest using the schedule's configuration
    without waiting for the scheduled time.
    """
    result = await db.execute(
        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    digest_id = await digest_scheduler.trigger_now(db, schedule_id)

    if digest_id:
        return {
            "message": "Schedule triggered successfully",
            "schedule_id": schedule_id,
            "digest_id": digest_id
        }
    else:
        return {
            "message": "Schedule triggered but no digest was created (possibly no papers found)",
            "schedule_id": schedule_id,
            "digest_id": None
        }


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle a schedule's active status."""
    result = await db.execute(
        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.is_active = not schedule.is_active
    schedule.updated_at = datetime.utcnow()

    await digest_scheduler.update_schedule(db, schedule)

    return {
        "id": schedule_id,
        "is_active": schedule.is_active,
        "message": f"Schedule {'activated' if schedule.is_active else 'deactivated'}"
    }


@router.get("/{schedule_id}/history", response_model=List[ScheduledDigestResponse])
async def get_schedule_history(
    schedule_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get history of digests generated by a schedule."""
    result = await db.execute(
        select(DigestSchedule).where(DigestSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    result = await db.execute(
        select(ScheduledDigest)
        .where(ScheduledDigest.schedule_id == schedule_id)
        .order_by(ScheduledDigest.triggered_at.desc())
        .limit(limit)
    )

    return result.scalars().all()


@router.get("/status/scheduler")
async def get_scheduler_status():
    """Get the status of the digest scheduler."""
    return {
        "available": digest_scheduler.is_available,
        "running": digest_scheduler._started,
        "message": (
            "Scheduler is running" if digest_scheduler._started
            else "Scheduler not started" if digest_scheduler.is_available
            else "APScheduler not installed"
        )
    }
