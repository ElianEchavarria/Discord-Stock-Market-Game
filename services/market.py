"""yfinance wrapper with a TTL price cache; blocking calls go through asyncio.to_thread."""

import asyncio
import time
import yfinance as yf
from config import PRICE_CACHE_TTL


_cache: dict = {}  # symbol -> (price, fetched_at)


class UnknownSymbol(Exception):
    """Raised when yfinance has no price for the symbol."""
    pass


def normalize(symbol: str) -> str:
    """Upper-case and strip a user-supplied ticker."""
    return symbol.strip().upper()


def _fetch_price(symbol: str) -> float:
    """Blocking yfinance lookup. Never call directly from the event loop."""
    ticker = yf.Ticker(symbol)
    price = ticker.info.get("regularMarketPrice")
    if price is None:
        raise UnknownSymbol(f"yfinance has no price for {symbol}")
    return price


async def get_price(symbol: str) -> float:
    """Return a cached price if fresh, else fetch via asyncio.to_thread and cache it."""
    symbol = normalize(symbol)
    now = time.time()
    cached = _cache.get(symbol)
    if cached is not None:
        price, fetched_at = cached
        if now - fetched_at < PRICE_CACHE_TTL:
            return price

    # Cache miss or stale; fetch and cache
    price = await asyncio.to_thread(_fetch_price, symbol)
    _cache[symbol] = (price, now)
    return price


async def get_prices(symbols) -> dict:
    """Quote several symbols at once; returns {symbol: price}."""
    symbols = [normalize(symbol) for symbol in symbols]
    fetched = await asyncio.gather(
        *(get_price(symbol) for symbol in symbols), return_exceptions=True
    )

    results = {}
    for symbol, price in zip(symbols, fetched):
        if isinstance(price, UnknownSymbol):
            results[symbol] = None
        elif isinstance(price, BaseException):
            raise price  # network/other errors still propagate
        else:
            results[symbol] = price
    return results


def clear_cache() -> None:
    """Drop every cached quote (used by tests)."""
    _cache.clear()
