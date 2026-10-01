"""aiosqlite setup and queries for users, holdings, and trades."""
from pathlib import Path

import aiosqlite
import config



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
    path = path or config.DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA)
        await db.commit()
        print(f"Initialized DB at {path}")


# --- users ---

async def create_user(user_id: int) -> bool:
    """Insert a user with STARTING_CASH. False if they already exist."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        result = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )

        user = await result.fetchone()
        if user is not None:
            return False  # user already exists
        await db.execute(
            "INSERT INTO users (user_id, cash) VALUES (?, ?)",
            (user_id, config.STARTING_CASH),
        )
        await db.commit()
        return True


async def get_user(user_id: int):
    """Return the user row, or None."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        result = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        return await result.fetchone()
    



async def update_cash(user_id: int, delta: float) -> None:
    """Add delta (negative to spend) to a user's cash."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET cash = cash + ? WHERE user_id = ?", (delta, user_id)
        )
        await db.commit()
    
    


# --- holdings ---

async def get_holding(user_id: int, symbol: str):
    """Return one holding row, or None."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        result = await db.execute(
            "SELECT * FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol)
        )
        return await result.fetchone()


async def get_holdings(user_id: int) -> list:
    """Every holding for a user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        result = await db.execute(
            "SELECT * FROM holdings WHERE user_id = ?", (user_id,)
        )
        return await result.fetchall()


async def upsert_holding(user_id: int, symbol: str, shares: float, avg_cost: float) -> None:
    """Insert or overwrite a holding; delete the row when shares hits 0."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        if shares <= 0:
            await db.execute(
                "DELETE FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol)
            )
        else:
            await db.execute(
                """
                INSERT INTO holdings (user_id, symbol, shares, avg_cost)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, symbol) DO UPDATE SET
                    shares = excluded.shares,
                    avg_cost = excluded.avg_cost
                """,
                (user_id, symbol, shares, avg_cost),
            )
        await db.commit()


# --- trades ---

async def log_trade(user_id: int, symbol: str, side: str, shares: float, price: float) -> None:
    """Append a trade to the ledger."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO trades (user_id, symbol, side, shares, price) VALUES (?, ?, ?, ?, ?)",
            (user_id, symbol, side, shares, price),
        )
        await db.commit()


async def get_trades(user_id: int, limit: int = 20) -> list:
    """Most recent trades for a user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        result = await db.execute(
            "SELECT * FROM trades WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return await result.fetchall()


# --- leaderboard ---

async def all_users_with_holdings() -> list:
    """Every user plus their holdings, for ranking by total value."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        result = await db.execute(
            """
            SELECT u.user_id, u.cash, h.symbol, h.shares, h.avg_cost
            FROM users u
            LEFT JOIN holdings h ON u.user_id = h.user_id
            """
        )
        return await result.fetchall()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
