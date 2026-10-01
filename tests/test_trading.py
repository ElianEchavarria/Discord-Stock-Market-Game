"""Buy/sell logic: insufficient funds, insufficient shares, average-cost math."""

import pytest
import pytest_asyncio

import config
from cogs.trading import Trading
from services import db, market

USER_ID = 1


class FakeAuthor:
    id = USER_ID
    display_name = "tester"
    mention = "@tester"


class FakeCtx:
    """Minimal stand-in for discord's Context that records what the cog sends."""

    def __init__(self):
        self.author = FakeAuthor()
        self.guild = None
        self.messages = []

    async def send(self, content=None, embed=None):
        self.messages.append(content if embed is None else embed)

    @property
    def text(self):
        """Last message flattened to a lowercase string, embed or not."""
        message = self.messages[-1]
        if isinstance(message, str):
            return message.lower()
        fields = " ".join(f"{f.name} {f.value}" for f in message.fields)
        return f"{message.title} {message.description} {fields}".lower()


class Game:
    """Drives cog commands against a throwaway database."""

    def __init__(self, cog, prices):
        self.cog = cog
        self.prices = prices

    async def run(self, command, *args) -> FakeCtx:
        ctx = FakeCtx()
        await getattr(self.cog, command).callback(self.cog, ctx, *args)
        return ctx

    def set_price(self, symbol, price):
        self.prices[symbol] = price
        market.clear_cache()  # otherwise the old quote is still fresh

    async def cash(self) -> float:
        return (await db.get_user(USER_ID))[1]

    async def holding(self, symbol="AAPL"):
        return await db.get_holding(USER_ID, symbol)


@pytest_asyncio.fixture
async def game(tmp_path, monkeypatch):
    """A started account, an empty database, and prices we control."""
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))

    prices = {"AAPL": 100.0, "MSFT": 200.0}

    def fake_fetch(symbol):
        if symbol not in prices:
            raise market.UnknownSymbol(symbol)
        return prices[symbol]

    monkeypatch.setattr(market, "_fetch_price", fake_fetch)
    market.clear_cache()

    await db.init_db()
    return Game(Trading(bot=None), prices)


# --- !start ---

@pytest.mark.asyncio
async def test_start_gives_10k(game):
    """!start creates the account with STARTING_CASH."""
    await game.run("start")
    assert await game.cash() == config.STARTING_CASH


@pytest.mark.asyncio
async def test_start_twice_rejected(game):
    """A second !start does not reset cash."""
    await game.run("start")
    await game.run("buy", "AAPL", 5)

    ctx = await game.run("start")
    assert "already have an account" in ctx.text
    assert await game.cash() == config.STARTING_CASH - 500


@pytest.mark.asyncio
async def test_commands_require_an_account(game):
    ctx = await game.run("buy", "AAPL", 5)
    assert "start" in ctx.text
    assert await db.get_user(USER_ID) is None


# --- !buy ---

@pytest.mark.asyncio
async def test_buy_debits_cash_and_adds_shares(game):
    await game.run("start")
    await game.run("buy", "AAPL", 5)

    assert await game.cash() == 9_500.0
    _, symbol, shares, avg_cost = await game.holding()
    assert (symbol, shares, avg_cost) == ("AAPL", 5.0, 100.0)


@pytest.mark.asyncio
async def test_buy_insufficient_funds(game):
    """A buy over the cash balance is rejected and changes nothing."""
    await game.run("start")
    ctx = await game.run("buy", "AAPL", 1_000)

    assert "not enough cash" in ctx.text
    assert await game.cash() == config.STARTING_CASH
    assert await game.holding() is None


@pytest.mark.asyncio
async def test_buy_unknown_symbol_changes_nothing(game):
    await game.run("start")
    ctx = await game.run("buy", "NOSUCH", 1)

    assert "couldn't find a price" in ctx.text
    assert await game.cash() == config.STARTING_CASH


@pytest.mark.asyncio
async def test_avg_cost_after_second_buy(game):
    """5 @ 100 then 5 @ 200 -> 10 shares at avg_cost 150."""
    await game.run("start")
    await game.run("buy", "AAPL", 5)
    game.set_price("AAPL", 200.0)
    await game.run("buy", "AAPL", 5)

    _, _, shares, avg_cost = await game.holding()
    assert shares == 10.0
    assert avg_cost == 150.0
    assert await game.cash() == config.STARTING_CASH - 500 - 1_000


@pytest.mark.asyncio
async def test_avg_cost_is_share_weighted(game):
    """Unequal lots: 5 @ 100 then 15 @ 200 -> 20 shares at 175, not 150.

    Equal lot sizes make a weighted and an unweighted average agree, so this
    is the case that actually proves the math.
    """
    await game.run("start")
    await game.run("buy", "AAPL", 5)
    game.set_price("AAPL", 200.0)
    await game.run("buy", "AAPL", 15)

    _, _, shares, avg_cost = await game.holding()
    assert shares == 20.0
    assert avg_cost == 175.0  # (5*100 + 15*200) / 20


# --- !sell ---

@pytest.mark.asyncio
async def test_sell_credits_cash_and_keeps_avg_cost(game):
    """Selling reduces shares but leaves avg_cost untouched."""
    await game.run("start")
    await game.run("buy", "AAPL", 10)
    game.set_price("AAPL", 150.0)
    await game.run("sell", "AAPL", 4)

    _, _, shares, avg_cost = await game.holding()
    assert shares == 6.0
    assert avg_cost == 100.0  # unchanged by the sale
    assert await game.cash() == 9_000.0 + 600.0


@pytest.mark.asyncio
async def test_sell_reports_realized_pnl(game):
    await game.run("start")
    await game.run("buy", "AAPL", 10)
    game.set_price("AAPL", 150.0)
    ctx = await game.run("sell", "AAPL", 4)

    assert "+$200.00" in ctx.text  # (150 - 100) * 4


@pytest.mark.asyncio
async def test_sell_more_than_held_rejected(game):
    await game.run("start")
    await game.run("buy", "AAPL", 5)
    ctx = await game.run("sell", "AAPL", 6)

    assert "you only hold" in ctx.text
    assert (await game.holding())[2] == 5.0


@pytest.mark.asyncio
async def test_sell_symbol_not_held_rejected(game):
    await game.run("start")
    ctx = await game.run("sell", "MSFT", 1)
    assert "don't own any" in ctx.text


@pytest.mark.asyncio
async def test_sell_all_removes_holding(game):
    await game.run("start")
    await game.run("buy", "AAPL", 5)
    await game.run("sell", "AAPL", 5)

    assert await game.holding() is None
    assert await game.cash() == config.STARTING_CASH


# --- quantity validation ---

@pytest.mark.parametrize("qty", [0, -1])
@pytest.mark.asyncio
async def test_negative_or_zero_qty_rejected(game, qty):
    await game.run("start")
    await game.run("buy", "AAPL", 10)

    buy = await game.run("buy", "AAPL", qty)
    sell = await game.run("sell", "AAPL", qty)

    assert "positive whole number" in buy.text
    assert "positive whole number" in sell.text
    assert (await game.holding())[2] == 10.0


# --- ledger ---

@pytest.mark.asyncio
async def test_trades_are_logged_newest_first(game):
    await game.run("start")
    await game.run("buy", "AAPL", 5)
    await game.run("sell", "AAPL", 2)

    trades = await db.get_trades(USER_ID)
    assert [(t[2], t[3], t[4]) for t in trades] == [
        ("AAPL", "SELL", 2.0),
        ("AAPL", "BUY", 5.0),
    ]
