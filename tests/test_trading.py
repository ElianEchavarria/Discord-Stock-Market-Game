"""Buy/sell logic: insufficient funds, insufficient shares, average-cost math."""

import pytest


@pytest.mark.asyncio
async def test_start_gives_10k():
    """!start creates the account with STARTING_CASH."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_start_twice_rejected():
    """A second !start does not reset cash."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_buy_debits_cash_and_adds_shares():
    # TODO
    ...


@pytest.mark.asyncio
async def test_buy_insufficient_funds():
    """A buy over the cash balance is rejected and changes nothing."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_avg_cost_after_second_buy():
    """5 @ 100 then 5 @ 200 -> 10 shares at avg_cost 150."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_sell_credits_cash_and_keeps_avg_cost():
    """Selling reduces shares but leaves avg_cost untouched."""
    # TODO
    ...


@pytest.mark.asyncio
async def test_sell_more_than_held_rejected():
    # TODO
    ...


@pytest.mark.asyncio
async def test_sell_all_removes_holding():
    # TODO
    ...


@pytest.mark.asyncio
async def test_negative_or_zero_qty_rejected():
    # TODO
    ...
