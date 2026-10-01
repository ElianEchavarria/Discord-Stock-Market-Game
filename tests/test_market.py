"""Price cache behavior with yfinance mocked out."""

import pytest


@pytest.fixture(autouse=True)
def clear_price_cache():
    """Reset the module-level cache between tests."""
    # TODO: services.market.clear_cache()
    yield
    # TODO: services.market.clear_cache()


@pytest.mark.asyncio
async def test_first_call_hits_yfinance(monkeypatch):
    # TODO
    ...


@pytest.mark.asyncio
async def test_second_call_within_ttl_uses_cache(monkeypatch):
    """One fetch for two calls inside PRICE_CACHE_TTL."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_cache_expires_after_ttl(monkeypatch):
    """Advance the clock past the TTL -> refetch."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_symbol_normalized(monkeypatch):
    """'aapl' and 'AAPL ' share one cache entry."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_unknown_symbol_raises(monkeypatch):
    # TODO
    ...


@pytest.mark.asyncio
async def test_failed_fetch_not_cached(monkeypatch):
    # TODO
    ...
