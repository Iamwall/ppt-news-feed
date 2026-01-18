"""Paper and news fetchers for various databases and sources.

Total: 53 fetchers across 5 categories + base classes.
"""
from app.fetchers.base import BaseFetcher, PaperData, BaseNewsFetcher, NewsData, AuthorData

# === CORE FETCHERS ===
from app.fetchers.pubmed import PubMedFetcher
from app.fetchers.arxiv import ArxivFetcher
from app.fetchers.biorxiv import BioRxivFetcher
from app.fetchers.semantic_scholar import SemanticScholarFetcher
from app.fetchers.plos import PLOSFetcher
from app.fetchers.rss_feeds import (
    NatureRSSFetcher, ScienceRSSFetcher, CellRSSFetcher,
    PLOSBiologyRSSFetcher, LancetRSSFetcher, NEJMRSSFetcher, BMJRSSFetcher,
)
from app.fetchers.custom_rss import CustomRSSFetcher

# === NEWS FETCHERS ===
from app.fetchers.news.hackernews import HackerNewsFetcher
from app.fetchers.news.reddit import RedditFetcher
from app.fetchers.news.gdelt import GDELTFetcher
from app.fetchers.news.wikinews import WikiNewsFetcher
from app.fetchers.news.datagov import DataGovFetcher

# === TECH FETCHERS ===
from app.fetchers.tech.github_trending import GitHubTrendingFetcher
from app.fetchers.tech.devto import DevToFetcher
from app.fetchers.tech.stackexchange import StackExchangeFetcher
from app.fetchers.tech.lobsters import LobstersFetcher
from app.fetchers.tech.haxor import HaxorFetcher
from app.fetchers.tech.huggingface import HuggingFaceFetcher

# === RESEARCH FETCHERS ===
from app.fetchers.research.openalex import OpenAlexFetcher
from app.fetchers.research.crossref import CrossrefFetcher
from app.fetchers.research.doaj import DOAJFetcher
from app.fetchers.research.zenodo import ZenodoFetcher
from app.fetchers.research.ssrn import SSRNFetcher
from app.fetchers.research.philpapers import PhilPapersFetcher
from app.fetchers.research.paperswithcode import PapersWithCodeFetcher

# === FINANCIAL FETCHERS ===
from app.fetchers.financial.coingecko import CoinGeckoFetcher
from app.fetchers.financial.yahoo_finance import YahooFinanceFetcher
from app.fetchers.financial.sec_edgar import SECEdgarFetcher
from app.fetchers.financial.cryptocompare import CryptoCompareFetcher
from app.fetchers.financial.worldbank import WorldBankFetcher

# === HEALTH FETCHERS ===
from app.fetchers.health.openfda import OpenFDAFetcher
from app.fetchers.health.clinicaltrials import ClinicalTrialsFetcher
from app.fetchers.health.europepmc import EuropePMCFetcher
from app.fetchers.health.who import WHOFetcher
from app.fetchers.health.cdc import CDCFetcher
from app.fetchers.health.medlineplus import MedlinePlusFetcher

# === OPTIONAL FETCHERS (require API keys or special packages) ===
_optional = {}

def _try_import(name, module, cls):
    try:
        mod = __import__(module, fromlist=[cls])
        _optional[name] = getattr(mod, cls)
    except Exception:
        pass

# News (API key required)
_try_import("newsapi", "app.fetchers.news.newsapi", "NewsAPIFetcher")
_try_import("mediastack", "app.fetchers.news.mediastack", "MediastackFetcher")
_try_import("praw", "app.fetchers.news.praw_fetcher", "PRAWFetcher")

# Financial (API key required)
_try_import("finnhub", "app.fetchers.financial.finnhub", "FinnhubFetcher")
_try_import("alphavantage", "app.fetchers.financial.alphavantage", "AlphaVantageFetcher")
_try_import("fred", "app.fetchers.financial.fred", "FREDFetcher")
_try_import("iexcloud", "app.fetchers.financial.iexcloud", "IEXCloudFetcher")
_try_import("polygon", "app.fetchers.financial.polygon", "PolygonFetcher")
_try_import("openbb", "app.fetchers.financial.openbb", "OpenBBFetcher")

# Research (API key required)
_try_import("unpaywall", "app.fetchers.research.unpaywall", "UnpaywallFetcher")
_try_import("core", "app.fetchers.research.core", "COREFetcher")
_try_import("nasaads", "app.fetchers.research.nasaads", "NASAADSFetcher")
_try_import("springer", "app.fetchers.research.springer", "SpringerFetcher")
_try_import("elsevier", "app.fetchers.research.elsevier", "ElsevierFetcher")

# Tech (API key or special package required)
_try_import("producthunt", "app.fetchers.tech.producthunt", "ProductHuntFetcher")
_try_import("librariesio", "app.fetchers.tech.librariesio", "LibrariesIOFetcher")
_try_import("pytrends", "app.fetchers.tech.pytrends", "PyTrendsFetcher")
_try_import("kaggle", "app.fetchers.tech.kaggle", "KaggleFetcher")

__all__ = [
    "BaseFetcher", "PaperData", "BaseNewsFetcher", "NewsData", "AuthorData",
    "PubMedFetcher", "ArxivFetcher", "BioRxivFetcher", "SemanticScholarFetcher",
    "PLOSFetcher", "CustomRSSFetcher",
]

# === FETCHER REGISTRY ===
FETCHER_REGISTRY = {
    # Scientific Research (20)
    "pubmed": PubMedFetcher,
    "arxiv": ArxivFetcher,
    "semantic_scholar": SemanticScholarFetcher,
    "openalex": OpenAlexFetcher,
    "crossref": CrossrefFetcher,
    "doaj": DOAJFetcher,
    "zenodo": ZenodoFetcher,
    "ssrn": SSRNFetcher,
    "philpapers": PhilPapersFetcher,
    "paperswithcode": PapersWithCodeFetcher,
    "biorxiv": BioRxivFetcher,
    "medrxiv": BioRxivFetcher,
    "plos": PLOSFetcher,
    "plos_biology_rss": PLOSBiologyRSSFetcher,
    "nature_rss": NatureRSSFetcher,
    "science_rss": ScienceRSSFetcher,
    "cell_rss": CellRSSFetcher,
    "lancet_rss": LancetRSSFetcher,
    "nejm_rss": NEJMRSSFetcher,
    "bmj_rss": BMJRSSFetcher,
    
    # Tech & Developer (10)
    "hackernews": HackerNewsFetcher,
    "github_trending": GitHubTrendingFetcher,
    "devto": DevToFetcher,
    "stackexchange": StackExchangeFetcher,
    "lobsters": LobstersFetcher,
    "haxor": HaxorFetcher,
    "huggingface": HuggingFaceFetcher,
    
    # News & Social (6)
    "reddit": RedditFetcher,
    "gdelt": GDELTFetcher,
    "wikinews": WikiNewsFetcher,
    "datagov": DataGovFetcher,
    
    # Financial (5)
    "coingecko": CoinGeckoFetcher,
    "yahoo_finance": YahooFinanceFetcher,
    "sec_edgar": SECEdgarFetcher,
    "cryptocompare": CryptoCompareFetcher,
    "worldbank": WorldBankFetcher,
    
    # Health (6)
    "openfda": OpenFDAFetcher,
    "clinicaltrials": ClinicalTrialsFetcher,
    "europepmc": EuropePMCFetcher,
    "who": WHOFetcher,
    "cdc": CDCFetcher,
    "medlineplus": MedlinePlusFetcher,
}

# Add optional fetchers
FETCHER_REGISTRY.update(_optional)

# Source categories
SOURCE_CATEGORIES = {
    "scientific": [
        "pubmed", "arxiv", "semantic_scholar", "openalex", "crossref", "doaj",
        "zenodo", "ssrn", "philpapers", "paperswithcode", "biorxiv", "medrxiv",
        "plos", "plos_biology_rss", "nature_rss", "science_rss", "cell_rss",
        "lancet_rss", "nejm_rss", "bmj_rss", "unpaywall", "core", "nasaads",
        "springer", "elsevier"
    ],
    "tech": [
        "hackernews", "github_trending", "devto", "stackexchange", "lobsters",
        "haxor", "huggingface", "producthunt", "librariesio", "pytrends", "kaggle"
    ],
    "news": ["reddit", "gdelt", "wikinews", "datagov", "newsapi", "mediastack", "praw"],
    "financial": [
        "coingecko", "yahoo_finance", "sec_edgar", "cryptocompare", "worldbank",
        "finnhub", "alphavantage", "fred", "iexcloud", "polygon", "openbb"
    ],
    "health": ["openfda", "clinicaltrials", "europepmc", "who", "cdc", "medlineplus"],
}

_custom_sources_cache: dict = {}


def register_custom_source(source_id: str, url: str, name: str, is_validated: bool = False, is_peer_reviewed: bool = False):
    _custom_sources_cache[source_id] = {"url": url, "name": name, "is_validated": is_validated, "is_peer_reviewed": is_peer_reviewed}


def get_fetcher(source: str, custom_source_info: dict = None):
    if source in FETCHER_REGISTRY:
        if source in ("biorxiv", "medrxiv"):
            return BioRxivFetcher(server=source)
        return FETCHER_REGISTRY[source]()
    if source.startswith("custom_"):
        info = custom_source_info or _custom_sources_cache.get(source)
        if info:
            return CustomRSSFetcher(source_id=source, feed_url=info["url"], source_name=info["name"],
                                   is_validated=info.get("is_validated", False), is_peer_reviewed=info.get("is_peer_reviewed", False))
    raise ValueError(f"Unknown source: {source}")


def get_sources_by_category(category: str) -> list:
    return SOURCE_CATEGORIES.get(category, [])


def get_all_categories() -> list:
    return list(SOURCE_CATEGORIES.keys())


def get_available_sources() -> dict:
    return {cat: [s for s in sources if s in FETCHER_REGISTRY] for cat, sources in SOURCE_CATEGORIES.items()}


def get_source_count() -> dict:
    available = get_available_sources()
    return {
        "total": len(FETCHER_REGISTRY),
        "by_category": {cat: len(sources) for cat, sources in available.items()},
    }
