"""Trading commands: !start, !buy, !sell, !price."""

# TODO: imports (discord, discord.ext.commands, config, services.db, services.market)


class Trading:  # TODO: subclass commands.Cog
    """Buying, selling, and quoting symbols."""

    def __init__(self, bot):
        self.bot = bot

    # @commands.command(name="start")
    async def start(self, ctx):
        """Create the caller's account with STARTING_CASH."""
        # TODO: reject if the user already exists
        ...

    # @commands.command(name="price")
    async def price(self, ctx, symbol: str):
        """Show the latest cached/live price for a symbol."""
        # TODO
        ...

    # @commands.command(name="buy")
    async def buy(self, ctx, symbol: str, qty: int):
        """Buy qty shares at the live price if the user can afford it."""
        # TODO: validate qty > 0, resolve price, check cash, update holding avg cost, log trade
        ...

    # @commands.command(name="sell")
    async def sell(self, ctx, symbol: str, qty: int):
        """Sell qty shares at the live price if the user holds enough."""
        # TODO: validate qty > 0, check held shares, credit cash, realize P&L, log trade
        ...


async def setup(bot):
    """discord.py extension hook."""
    # TODO: await bot.add_cog(Trading(bot))
    ...
