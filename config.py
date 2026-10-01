"""Constants: starting cash, cache TTL, leaderboard schedule."""
import os

from dotenv import load_dotenv

load_dotenv()

COMMAND_PREFIX = "!"

# --- Game rules ---
STARTING_CASH = 10_000.00
MAX_SYMBOL_LEN = 8

# --- Market data ---
PRICE_CACHE_TTL = 60  # seconds a cached quote stays fresh

# --- Persistence ---
DB_PATH = "data/market.db"

# --- Weekly leaderboard ---
LEADERBOARD_DAY = 4  # 0 = Monday ... 6 = Sunday
LEADERBOARD_HOUR = 16  # local time, 24h
_channel_id = os.getenv("LEADERBOARD_CHANNEL_ID")
LEADERBOARD_CHANNEL_ID = int(_channel_id) if _channel_id else None

# --- Display ---
EMBED_COLOR = 0x2ECC71
LEADERBOARD_TOP_N = 10
