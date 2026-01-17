# Database models
from app.models.paper import Paper, Author
from app.models.digest import Digest, DigestPaper
from app.models.app_settings import AppSettings
from app.models.fetch_job import FetchJob
from app.models.domain_config import DomainConfig, DEFAULT_DOMAINS
from app.models.custom_source import CustomSource

__all__ = [
    "Paper",
    "Author",
    "Digest",
    "DigestPaper",
    "AppSettings",
    "FetchJob",
    "DomainConfig",
    "DEFAULT_DOMAINS",
    "CustomSource",
]
