"""yfinance wrapper with a TTL price cache; blocking calls go through asyncio.to_thread."""

# TODO: imports (asyncio, time, yfinance, config.PRICE_CACHE_TTL)

_cache: dict = {}  # symbol -> (price, fetched_at)


class UnknownSymbol(Exception):
    """Raised when yfinance has no price for the symbol."""


def normalize(symbol: str) -> str:
    """Upper-case and strip a user-supplied ticker."""
    # TODO
    ...


def _fetch_price(symbol: str) -> float:
    """Blocking yfinance lookup. Never call directly from the event loop."""
    # TODO
    ...


async def get_price(symbol: str) -> float:
    """Return a cached price if fresh, else fetch via asyncio.to_thread and cache it."""
    # TODO
    ...


async def get_prices(symbols) -> dict:
    """Quote several symbols at once; returns {symbol: price}."""
    # TODO
    ...


def clear_cache() -> None:
    """Drop every cached quote (used by tests)."""
    # TODO
    ...
