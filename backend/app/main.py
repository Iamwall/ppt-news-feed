"""Main FastAPI application entry point."""
# Updated for summary infographics support
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.api import router as api_router

# Ensure directories exist before app initialization
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.generated_images_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    
    yield
    
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    description="Aggregates scientific papers from multiple databases, generates AI summaries with credibility analysis, and creates newsletters.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for generated images
app.mount("/static/images", StaticFiles(directory=settings.generated_images_dir), name="images")

# API routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
