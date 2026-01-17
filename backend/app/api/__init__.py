"""API routes initialization."""
from fastapi import APIRouter

from app.api import papers, digests, settings as settings_routes, fetch, newsletters, demo

router = APIRouter()

router.include_router(papers.router, prefix="/papers", tags=["papers"])
router.include_router(digests.router, prefix="/digests", tags=["digests"])
router.include_router(settings_routes.router, prefix="/settings", tags=["settings"])
router.include_router(fetch.router, prefix="/fetch", tags=["fetch"])
router.include_router(newsletters.router, prefix="/newsletters", tags=["newsletters"])
router.include_router(demo.router, prefix="/demo", tags=["demo"])