# Discord Stock Market Game

A Discord bot that runs a paper-trading game on **live market data**. Everyone starts
with $10,000 of fake money, trades real tickers at real prices from
[yfinance](https://pypi.org/project/yfinance/), and gets ranked on a weekly leaderboard.

Portfolios persist in SQLite, so balances survive restarts.

<!-- TODO: screenshot / GIF of !portfolio and the weekly leaderboard -->

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your bot token in
python bot.py
```

The bot needs the **Message Content Intent** enabled in the
[Discord Developer Portal](https://discord.com/developers/applications), plus the
`bot` scope with Send Messages / Embed Links / Attach Files permissions.

## Commands

| Command | What it does |
| --- | --- |
| `!start` | Open an account with $10,000 |
| `!price AAPL` | Latest price for a ticker |
| `!buy AAPL 5` | Buy 5 shares at the live price |
| `!sell AAPL 5` | Sell 5 shares at the live price |
| `!portfolio` | Cash, holdings, market value, unrealized P&L |
| `!leaderboard` | Current ranking by total portfolio value |

A leaderboard is also posted automatically once a week (see `config.py`).

## Configuration

Game rules live in [config.py](config.py) — starting cash, price-cache TTL, and the
weekly leaderboard day/hour/channel. Secrets live in `.env` (see `.env.example`).

## Tests

```bash
pytest
```

## Project layout

```
bot.py          entry point: loads the token, starts the bot, loads cogs
config.py       starting cash, cache TTL, leaderboard schedule
cogs/           Discord command groups (trading, portfolio)
services/       market data, database, charts
tests/          trading logic + cache behavior
data/           SQLite file (gitignored)
```
