"""Optional matplotlib renderings: portfolio allocation and P&L images."""

# TODO: imports (io, asyncio, matplotlib (use the Agg backend), discord.File)


def _render_allocation(holdings) -> bytes:
    """Blocking render of an allocation pie/bar chart to PNG bytes."""
    # TODO
    ...


def _render_pnl(history) -> bytes:
    """Blocking render of a P&L line chart to PNG bytes."""
    # TODO
    ...


async def allocation_chart(holdings):
    """Return a discord.File of the allocation chart (via asyncio.to_thread)."""
    # TODO
    ...


async def pnl_chart(history):
    """Return a discord.File of the P&L chart (via asyncio.to_thread)."""
    # TODO
    ...
