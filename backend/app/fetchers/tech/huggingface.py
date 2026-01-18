"""Hugging Face Hub API fetcher for ML models.

https://huggingface.co/docs/hub/api
No API key required for public data.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseNewsFetcher, NewsData


class HuggingFaceFetcher(BaseNewsFetcher):
    """Fetcher for Hugging Face models and datasets."""
    
    source_name = "huggingface"
    category = "tech"
    rate_limit = 2.0
    requires_api_key = False
    
    BASE_URL = "https://huggingface.co/api"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch trending models from Hugging Face."""
        await self._rate_limit()
        
        params = {
            "limit": min(max_results, 100),
            "sort": "downloads",
            "direction": "-1",
        }
        
        if keywords:
            params["search"] = " ".join(keywords)
        
        async with httpx.AsyncClient() as client:
            # Get models
            response = await client.get(
                f"{self.BASE_URL}/models",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            models = response.json()
        
        for model in models[:max_results // 2]:
            model_id = model.get("modelId", model.get("id", ""))
            if not model_id:
                continue
            
            # Parse date
            pub_date = None
            if model.get("lastModified"):
                try:
                    pub_date = datetime.fromisoformat(model["lastModified"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            yield NewsData(
                title=f"HF Model: {model_id}",
                summary=model.get("description"),
                source=self.source_name,
                source_id=f"model_{model_id}",
                url=f"https://huggingface.co/{model_id}",
                published_date=pub_date,
                author=model_id.split("/")[0] if "/" in model_id else None,
                category=self.category,
                tags=["huggingface", "ml", "model"] + model.get("tags", [])[:5],
                raw_data={
                    "downloads": model.get("downloads"),
                    "likes": model.get("likes"),
                    "pipeline_tag": model.get("pipeline_tag"),
                }
            )
        
        # Also get datasets
        await self._rate_limit()
        
        response = await httpx.AsyncClient().get(
            f"{self.BASE_URL}/datasets",
            params=params,
            timeout=60.0,
        )
        response.raise_for_status()
        datasets = response.json()
        
        for ds in datasets[:max_results // 2]:
            ds_id = ds.get("id", "")
            if not ds_id:
                continue
            
            yield NewsData(
                title=f"HF Dataset: {ds_id}",
                summary=ds.get("description"),
                source=self.source_name,
                source_id=f"dataset_{ds_id}",
                url=f"https://huggingface.co/datasets/{ds_id}",
                published_date=datetime.now(timezone.utc),
                author=ds_id.split("/")[0] if "/" in ds_id else None,
                category=self.category,
                tags=["huggingface", "ml", "dataset"],
                raw_data={
                    "downloads": ds.get("downloads"),
                }
            )
