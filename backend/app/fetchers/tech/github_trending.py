"""GitHub Trending fetcher.

Unofficial API for GitHub trending repos.
No API key required. Scrapes the trending page.
"""
from datetime import datetime, timezone
from typing import Optional, List, AsyncIterator
import httpx
from bs4 import BeautifulSoup

from app.fetchers.base import BaseNewsFetcher, NewsData


class GitHubTrendingFetcher(BaseNewsFetcher):
    """Fetcher for GitHub trending repositories."""
    
    source_name = "github_trending"
    category = "tech"
    rate_limit = 1.0  # Be polite
    requires_api_key = False
    
    BASE_URL = "https://github.com/trending"
    
    async def fetch(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        days_back: int = 7,
    ) -> AsyncIterator[NewsData]:
        """Fetch trending repositories from GitHub.
        
        Keywords are used to filter by programming language.
        """
        await self._rate_limit()
        
        # Map days_back to GitHub's time range
        if days_back <= 1:
            since = "daily"
        elif days_back <= 7:
            since = "weekly"
        else:
            since = "monthly"
        
        # If keywords look like languages, use first one
        language = ""
        if keywords:
            # Common programming languages
            lang_keywords = ["python", "javascript", "typescript", "rust", "go", 
                          "java", "c++", "c#", "ruby", "swift", "kotlin"]
            for kw in keywords:
                if kw.lower() in lang_keywords:
                    language = kw.lower()
                    break
        
        url = self.BASE_URL
        if language:
            url = f"{url}/{language}"
        
        params = {"since": since}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PPT-NewsFeed/1.0)"}
            )
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all repository articles
        repo_articles = soup.select("article.Box-row")
        
        count = 0
        for article in repo_articles:
            if count >= max_results:
                break
            
            try:
                # Repository name and link
                h2 = article.select_one("h2")
                if not h2:
                    continue
                
                link = h2.select_one("a")
                if not link:
                    continue
                
                repo_path = link.get("href", "").strip("/")
                if not repo_path:
                    continue
                
                parts = repo_path.split("/")
                if len(parts) < 2:
                    continue
                
                owner, repo_name = parts[0], parts[1]
                full_name = f"{owner}/{repo_name}"
                
                # Filter by other keywords (not language)
                if keywords and language:
                    # Filter by non-language keywords
                    other_keywords = [k for k in keywords if k.lower() != language]
                    if other_keywords:
                        combined = full_name.lower()
                        desc_elem = article.select_one("p")
                        if desc_elem:
                            combined += " " + desc_elem.get_text().lower()
                        if not any(kw.lower() in combined for kw in other_keywords):
                            continue
                elif keywords and not language:
                    # All keywords are for filtering
                    combined = full_name.lower()
                    desc_elem = article.select_one("p")
                    if desc_elem:
                        combined += " " + desc_elem.get_text().lower()
                    if not any(kw.lower() in combined for kw in keywords):
                        continue
                
                # Description
                desc_elem = article.select_one("p")
                description = desc_elem.get_text().strip() if desc_elem else None
                
                # Language
                lang_elem = article.select_one("[itemprop='programmingLanguage']")
                lang = lang_elem.get_text().strip() if lang_elem else None
                
                # Stars
                stars_elem = article.select_one("a[href*='/stargazers']")
                stars = stars_elem.get_text().strip().replace(",", "") if stars_elem else "0"
                
                # Stars today
                stars_today_elem = article.select_one("span.d-inline-block.float-sm-right")
                stars_today = stars_today_elem.get_text().strip() if stars_today_elem else None
                
                yield NewsData(
                    title=f"Trending: {full_name}",
                    summary=description or f"Trending {lang or 'repository'} on GitHub",
                    source=self.source_name,
                    source_id=repo_path.replace("/", "_"),
                    url=f"https://github.com/{repo_path}",
                    published_date=datetime.now(timezone.utc),
                    author=owner,
                    category=self.category,
                    tags=["github", "trending", lang.lower() if lang else "code"],
                    raw_data={
                        "stars": stars,
                        "stars_today": stars_today,
                        "language": lang,
                        "owner": owner,
                        "repo": repo_name,
                    }
                )
                count += 1
                
            except Exception as e:
                print(f"Error parsing GitHub trending repo: {e}")
                continue
