
import pytest
from app.api.sources import BUILTIN_SOURCES
from app.fetchers import FETCHER_REGISTRY

def test_sources_synchronization():
    """
    Verify that all BUILTIN_SOURCES in api/sources.py have a corresponding
    fetcher in FETCHER_REGISTRY (app/fetchers/__init__.py).
    """
    builtin_keys = set(BUILTIN_SOURCES.keys())
    registry_keys = set(FETCHER_REGISTRY.keys())
    
    # Check for sources in API but missing in Registry
    missing_in_registry = builtin_keys - registry_keys
    assert not missing_in_registry, f"Sources defined in API but missing fetcher implementation: {missing_in_registry}"
    
    # Check for sources in Registry but missing in API (Optional, but good for consistency)
    # missing_in_api = registry_keys - builtin_keys
    # assert not missing_in_api, f"Fetchers registered but not exposed in API: {missing_in_api}"
