"""Price cache behavior with yfinance mocked out."""

import pytest

import config
from services import market


class FakeClock:
    """Stands in for the time module so tests can jump forward."""

    def __init__(self, start=1_000.0):
        self.now = start

    def time(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(market, "time", fake)
    return fake


@pytest.fixture
def fetches(monkeypatch):
    """Replace the blocking yfinance call; returns the list of symbols asked for."""
    calls = []

    def fake_fetch(symbol):
        calls.append(symbol)
        if symbol == "NOSUCH":
            raise market.UnknownSymbol(symbol)
        return 100.0

    monkeypatch.setattr(market, "_fetch_price", fake_fetch)
    return calls


@pytest.fixture(autouse=True)
def clear_price_cache():
    """Reset the module-level cache between tests."""
    market.clear_cache()
    yield
    market.clear_cache()


@pytest.mark.asyncio
async def test_first_call_hits_yfinance(fetches, clock):
    assert await market.get_price("AAPL") == 100.0
    assert fetches == ["AAPL"]


@pytest.mark.asyncio
async def test_second_call_within_ttl_uses_cache(fetches, clock):
    """One fetch for two calls inside PRICE_CACHE_TTL."""
    await market.get_price("AAPL")
    clock.advance(config.PRICE_CACHE_TTL - 1)
    await market.get_price("AAPL")
    assert fetches == ["AAPL"]


@pytest.mark.asyncio
async def test_cache_expires_after_ttl(fetches, clock):
    """Advance the clock past the TTL -> refetch."""
    await market.get_price("AAPL")
    clock.advance(config.PRICE_CACHE_TTL + 1)
    await market.get_price("AAPL")
    assert fetches == ["AAPL", "AAPL"]


@pytest.mark.asyncio
async def test_symbol_normalized(fetches, clock):
    """'aapl' and 'AAPL ' share one cache entry."""
    await market.get_price("aapl")
    await market.get_price("AAPL ")
    assert fetches == ["AAPL"]
    assert list(market._cache) == ["AAPL"]


@pytest.mark.asyncio
async def test_unknown_symbol_raises(fetches, clock):
    with pytest.raises(market.UnknownSymbol):
        await market.get_price("NOSUCH")


@pytest.mark.asyncio
async def test_failed_fetch_not_cached(fetches, clock):
    """A transient failure must not poison the symbol for a whole TTL."""
    with pytest.raises(market.UnknownSymbol):
        await market.get_price("NOSUCH")
    assert market._cache == {}

    with pytest.raises(market.UnknownSymbol):
        await market.get_price("NOSUCH")
    assert fetches == ["NOSUCH", "NOSUCH"]  # retried, not served from cache


@pytest.mark.asyncio
async def test_clear_cache_forces_refetch(fetches, clock):
    await market.get_price("AAPL")
    market.clear_cache()
    await market.get_price("AAPL")
    assert fetches == ["AAPL", "AAPL"]


# --- get_prices ---

@pytest.mark.asyncio
async def test_get_prices_normalizes_keys(fetches, clock):
    """Keys come back normalized, so callers can look up 'AAPL' reliably."""
    assert await market.get_prices(["aapl", " msft "]) == {"AAPL": 100.0, "MSFT": 100.0}


@pytest.mark.asyncio
async def test_get_prices_unknown_symbol_is_none(fetches, clock):
    """One bad ticker must not sink the whole batch."""
    assert await market.get_prices(["AAPL", "NOSUCH"]) == {"AAPL": 100.0, "NOSUCH": None}


@pytest.mark.asyncio
async def test_get_prices_propagates_real_errors(monkeypatch, clock):
    """Network failures are not swallowed the way unknown symbols are."""

    def boom(symbol):
        raise ConnectionError("network down")

    monkeypatch.setattr(market, "_fetch_price", boom)
    with pytest.raises(ConnectionError):
        await market.get_prices(["AAPL"])


@pytest.mark.asyncio
async def test_get_prices_uses_cache(fetches, clock):
    await market.get_price("AAPL")
    await market.get_prices(["AAPL", "MSFT"])
    assert fetches == ["AAPL", "MSFT"]  # AAPL served from cache
