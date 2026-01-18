"""Kaggle API fetcher for data science.

https://www.kaggle.com/docs/api
Requires API credentials.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import os
import asyncio

from app.fetchers.base import BaseNewsFetcher, NewsData


class KaggleFetcher(BaseNewsFetcher):
    """Fetcher for Kaggle datasets and competitions."""
    
    source_name = "kaggle"
    category = "tech"
    rate_limit = 1.0
    requires_api_key = True
    
    def __init__(self, username: Optional[str] = None, key: Optional[str] = None):
        super().__init__()
        self.username = username or os.getenv("KAGGLE_USERNAME")
        self.key = key or os.getenv("KAGGLE_KEY")
        
        if not self.username or not self.key:
            raise ValueError("KAGGLE_USERNAME and KAGGLE_KEY required")
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch datasets and competitions from Kaggle."""
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            raise ImportError("kaggle not installed. Run: pip install kaggle")
        
        await self._rate_limit()
        
        loop = asyncio.get_event_loop()
        
        # Initialize Kaggle API
        api = KaggleApi()
        api.authenticate()
        
        # Search datasets
        try:
            search_term = " ".join(keywords) if keywords else ""
            datasets = await loop.run_in_executor(
                None,
                lambda: api.dataset_list(search=search_term, sort_by="hottest", page_size=max_results // 2)
            )
            
            for ds in datasets:
                yield NewsData(
                    title=f"Kaggle Dataset: {ds.title}",
                    summary=ds.subtitle if hasattr(ds, 'subtitle') else None,
                    source=self.source_name,
                    source_id=f"dataset_{ds.ref}",
                    url=f"https://www.kaggle.com/datasets/{ds.ref}",
                    published_date=ds.lastUpdated if hasattr(ds, 'lastUpdated') else datetime.now(timezone.utc),
                    author=ds.ownerName if hasattr(ds, 'ownerName') else None,
                    category=self.category,
                    tags=["kaggle", "dataset", "data-science"],
                    raw_data={
                        "size": ds.totalBytes if hasattr(ds, 'totalBytes') else None,
                        "usabilityRating": ds.usabilityRating if hasattr(ds, 'usabilityRating') else None,
                    }
                )
        except Exception as e:
            print(f"Kaggle datasets error: {e}")
        
        # Get competitions
        try:
            competitions = await loop.run_in_executor(
                None,
                lambda: api.competitions_list(search=search_term if keywords else "", sort_by="latestDeadline")
            )
            
            for comp in competitions[:max_results // 2]:
                yield NewsData(
                    title=f"Kaggle Competition: {comp.title}",
                    summary=comp.description if hasattr(comp, 'description') else None,
                    source=self.source_name,
                    source_id=f"competition_{comp.ref}",
                    url=f"https://www.kaggle.com/competitions/{comp.ref}",
                    published_date=comp.enabledDate if hasattr(comp, 'enabledDate') else datetime.now(timezone.utc),
                    author="Kaggle",
                    category=self.category,
                    tags=["kaggle", "competition", "ml"],
                    raw_data={
                        "reward": comp.reward if hasattr(comp, 'reward') else None,
                        "deadline": str(comp.deadline) if hasattr(comp, 'deadline') else None,
                    }
                )
        except Exception as e:
            print(f"Kaggle competitions error: {e}")
