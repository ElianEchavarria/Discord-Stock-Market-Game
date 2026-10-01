"""aiosqlite setup and queries for users, holdings, and trades."""

# TODO: imports (aiosqlite, config.DB_PATH, config.STARTING_CASH)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY,
    cash      REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS holdings (
    user_id   INTEGER NOT NULL,
    symbol    TEXT    NOT NULL,
    shares    REAL    NOT NULL,
    avg_cost  REAL    NOT NULL,
    PRIMARY KEY (user_id, symbol),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS trades (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL,
    symbol    TEXT    NOT NULL,
    side      TEXT    NOT NULL CHECK (side IN ('BUY', 'SELL')),
    shares    REAL    NOT NULL,
    price     REAL    NOT NULL,
    ts        TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""


async def init_db(path: str = None) -> None:
    """Create the data dir and run SCHEMA."""
    # TODO
    ...


# --- users ---

async def create_user(user_id: int) -> bool:
    """Insert a user with STARTING_CASH. False if they already exist."""
    # TODO
    ...


async def get_user(user_id: int):
    """Return the user row, or None."""
    # TODO
    ...


async def update_cash(user_id: int, delta: float) -> None:
    """Add delta (negative to spend) to a user's cash."""
    # TODO
    ...


# --- holdings ---

async def get_holding(user_id: int, symbol: str):
    """Return one holding row, or None."""
    # TODO
    ...


async def get_holdings(user_id: int) -> list:
    """Every holding for a user."""
    # TODO
    ...


async def upsert_holding(user_id: int, symbol: str, shares: float, avg_cost: float) -> None:
    """Insert or overwrite a holding; delete the row when shares hits 0."""
    # TODO
    ...


# --- trades ---

async def log_trade(user_id: int, symbol: str, side: str, shares: float, price: float) -> None:
    """Append a trade to the ledger."""
    # TODO
    ...


async def get_trades(user_id: int, limit: int = 20) -> list:
    """Most recent trades for a user."""
    # TODO
    ...


# --- leaderboard ---

async def all_users_with_holdings() -> list:
    """Every user plus their holdings, for ranking by total value."""
    # TODO
    ...
