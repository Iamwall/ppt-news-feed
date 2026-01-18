"""ClinicalTrials.gov API fetcher.

https://clinicaltrials.gov/data-api/api
No API key required. Rate limit: 3 requests/second.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import httpx

from app.fetchers.base import BaseFetcher, PaperData, AuthorData


class ClinicalTrialsFetcher(BaseFetcher):
    """Fetcher for ClinicalTrials.gov clinical trial data."""
    
    source_name = "clinicaltrials"
    rate_limit = 3.0
    
    BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch clinical trials from ClinicalTrials.gov."""
        await self._rate_limit()
        
        # Calculate date range
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        params = {
            "format": "json",
            "pageSize": min(max_results, 100),
            "sort": "LastUpdatePostDate:desc",
        }
        
        # Build query
        query_parts = []
        if keywords:
            for kw in keywords:
                query_parts.append(f"AREA[Condition] {kw} OR AREA[InterventionName] {kw}")
        
        if query_parts:
            params["query.cond"] = " OR ".join(keywords) if keywords else ""
        
        # Filter by date
        params["filter.advanced"] = f"AREA[LastUpdatePostDate]RANGE[{from_date.strftime('%Y-%m-%d')},MAX]"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/studies",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        studies = data.get("studies", [])
        
        for study in studies:
            try:
                paper = self._parse_study(study)
                if paper:
                    yield paper
            except Exception as e:
                print(f"Error parsing clinical trial: {e}")
                continue
    
    def _parse_study(self, study: dict) -> Optional[PaperData]:
        """Parse a single clinical trial study."""
        protocol = study.get("protocolSection", {})
        
        # Identification
        id_module = protocol.get("identificationModule", {})
        nct_id = id_module.get("nctId")
        title = id_module.get("officialTitle") or id_module.get("briefTitle")
        
        if not title or not nct_id:
            return None
        
        # Description
        desc_module = protocol.get("descriptionModule", {})
        abstract = desc_module.get("briefSummary") or desc_module.get("detailedDescription")
        
        # Status
        status_module = protocol.get("statusModule", {})
        
        # Parse dates
        pub_date = None
        last_update = status_module.get("lastUpdatePostDateStruct", {}).get("date")
        if last_update:
            try:
                pub_date = datetime.strptime(last_update, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        # Sponsors/Contacts as authors
        authors = []
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        if lead_sponsor.get("name"):
            authors.append(AuthorData(
                name=lead_sponsor.get("name"),
                affiliation=lead_sponsor.get("class"),
            ))
        
        # Collaborators
        collaborators = sponsor_module.get("collaborators", [])
        for collab in collaborators[:5]:
            if collab.get("name"):
                authors.append(AuthorData(
                    name=collab.get("name"),
                    affiliation=collab.get("class"),
                ))
        
        # Conditions being studied
        conditions_module = protocol.get("conditionsModule", {})
        conditions = conditions_module.get("conditions", [])
        
        # Interventions
        arms_module = protocol.get("armsInterventionsModule", {})
        interventions = arms_module.get("interventions", [])
        intervention_names = [i.get("name") for i in interventions if i.get("name")]
        
        return PaperData(
            title=title,
            abstract=abstract[:2000] if abstract and len(abstract) > 2000 else abstract,
            authors=authors,
            source=self.source_name,
            source_id=nct_id,
            journal="ClinicalTrials.gov",
            url=f"https://clinicaltrials.gov/study/{nct_id}",
            published_date=pub_date,
            is_peer_reviewed=False,
            is_preprint=False,
            raw_data={
                "status": status_module.get("overallStatus"),
                "phase": status_module.get("phases", []),
                "conditions": conditions,
                "interventions": intervention_names,
                "enrollment": protocol.get("designModule", {}).get("enrollmentInfo", {}).get("count"),
            }
        )
