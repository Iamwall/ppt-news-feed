from datetime import datetime, timedelta, timezone
from typing import Optional, List, AsyncIterator
import asyncio
import httpx
from xml.etree import ElementTree

from app.fetchers.base import BaseFetcher, PaperData, AuthorData
from app.core.config import settings


class PubMedFetcher(BaseFetcher):
    """Fetcher for PubMed using E-utilities API."""
    
    source_name = "pubmed"
    rate_limit = settings.pubmed_requests_per_second
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[PaperData]:
        """Fetch papers from PubMed."""
        
        # Build search query
        query_parts = []
        if keywords:
            query_parts.append(" OR ".join(f'"{k}"[Title/Abstract]' for k in keywords))
        
        # Add date filter
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
        to_date = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        query_parts.append(f'("{from_date}"[Date - Publication] : "{to_date}"[Date - Publication])')
        
        query = " AND ".join(query_parts) if query_parts else "*"
        
        # Search for PMIDs
        pmids = await self._search(query, max_results)
        
        if not pmids:
            return
        
        # Fetch details in batches
        batch_size = 20
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            papers = await self._fetch_details(batch)
            for paper in papers:
                yield paper
    
    async def _search(self, query: str, max_results: int) -> List[str]:
        """Search PubMed and return PMIDs."""
        await self._rate_limit()
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
            "tool": "ScienceDigest",
            "email": settings.email_from,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
        return data.get("esearchresult", {}).get("idlist", [])
    
    async def _fetch_details(self, pmids: List[str]) -> List[PaperData]:
        """Fetch paper details for given PMIDs."""
        await self._rate_limit()
        
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "tool": "ScienceDigest",
            "email": settings.email_from,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()
        
        # Parse XML response
        root = ElementTree.fromstring(response.content)
        papers = []
        
        for article in root.findall(".//PubmedArticle"):
            try:
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)
            except Exception as e:
                # Log error but continue processing
                print(f"Error parsing PubMed article: {e}")
                continue
        
        return papers
    
    def _parse_article(self, article: ElementTree.Element) -> Optional[PaperData]:
        """Parse a single PubMed article XML element."""
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None
        
        # Get PMID
        pmid_elem = medline.find("PMID")
        if pmid_elem is None:
            return None
        pmid = pmid_elem.text
        
        # Get article info
        article_elem = medline.find("Article")
        if article_elem is None:
            return None
        
        # Title
        title_elem = article_elem.find("ArticleTitle")
        title = title_elem.text if title_elem is not None else "Untitled"
        
        # Abstract - handle both simple and structured abstracts
        # Use itertext() to capture all text including child elements (e.g., <i>, <b>)
        abstract = None
        abstract_texts = article_elem.findall(".//AbstractText")
        
        if abstract_texts:
            abstract_parts = []
            for abs_text in abstract_texts:
                # Get all text content including text in child elements
                full_text = "".join(abs_text.itertext()).strip()
                
                if full_text:
                    label = abs_text.get("Label", "")
                    if label:
                        abstract_parts.append(f"{label}: {full_text}")
                    else:
                        abstract_parts.append(full_text)
            
            abstract = " ".join(abstract_parts) if abstract_parts else None
        
        # Journal
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else None
        
        # Authors
        authors = []
        author_list = article_elem.find("AuthorList")
        if author_list is not None:
            for author_elem in author_list.findall("Author"):
                last_name = author_elem.find("LastName")
                first_name = author_elem.find("ForeName")
                if last_name is not None:
                    name = f"{first_name.text if first_name is not None else ''} {last_name.text}".strip()
                    
                    # Affiliation
                    affil_elem = author_elem.find(".//Affiliation")
                    affiliation = affil_elem.text if affil_elem is not None else None
                    
                    authors.append(AuthorData(name=name, affiliation=affiliation))
        
        # Publication date
        pub_date = None
        date_elem = article_elem.find(".//PubDate")
        if date_elem is not None:
            year = date_elem.find("Year")
            month = date_elem.find("Month")
            day = date_elem.find("Day")
            if year is not None:
                try:
                    year_val = int(year.text)
                    month_val = self._parse_month(month.text) if month is not None else 1
                    day_val = int(day.text) if day is not None else 1
                    pub_date = datetime(year_val, month_val, day_val)
                except (ValueError, TypeError):
                    pass
        
        # DOI
        doi = None
        for id_elem in article.findall(".//ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text
                break
        
        return PaperData(
            title=title,
            abstract=abstract,
            authors=authors,
            source=self.source_name,
            source_id=pmid,
            journal=journal,
            doi=doi,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            published_date=pub_date,
            is_peer_reviewed=True,
            is_preprint=False,
        )
    
    def _parse_month(self, month_str: str) -> int:
        """Parse month string to integer."""
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        try:
            return int(month_str)
        except ValueError:
            return months.get(month_str.lower()[:3], 1)
