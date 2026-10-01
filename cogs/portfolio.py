"""Portfolio commands: !portfolio, !leaderboard, plus the weekly leaderboard task."""

# TODO: imports (discord, discord.ext.commands/tasks, config, services.db, services.market)


class Portfolio:  # TODO: subclass commands.Cog
    """Holdings, P&L, and rankings."""

    def __init__(self, bot):
        self.bot = bot
        # TODO: self.weekly_leaderboard.start()

    def cog_unload(self):
        # TODO: self.weekly_leaderboard.cancel()
        ...

    # @commands.command(name="portfolio")
    async def portfolio(self, ctx, member=None):
        """Show cash, holdings, market value, and unrealized P&L."""
        # TODO: fetch holdings, batch-quote symbols, build embed (chart optional)
        ...

    # @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """Rank users in this guild by total portfolio value."""
        # TODO
        ...

    # --- Background task ---

    # @tasks.loop(hours=1)
    async def weekly_leaderboard(self):
        """Post the leaderboard once a week per LEADERBOARD_DAY/HOUR."""
        # TODO: check day/hour, guard against double-posting, send to LEADERBOARD_CHANNEL_ID
        ...

    # @weekly_leaderboard.before_loop
    async def before_weekly_leaderboard(self):
        # TODO: await self.bot.wait_until_ready()
        ...


async def setup(bot):
    """discord.py extension hook."""
    # TODO: await bot.add_cog(Portfolio(bot))
    ...
