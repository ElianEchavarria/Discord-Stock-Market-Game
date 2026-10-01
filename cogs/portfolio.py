"""Portfolio commands: !portfolio, !leaderboard, plus the weekly leaderboard task."""

from datetime import datetime

import discord
from discord.ext import commands, tasks

import config
from cogs.trading import money
from services import db, market


def value_of(shares: float, avg_cost: float, price) -> tuple:
    """Return (market_value, cost_basis). Falls back to cost when price is unknown."""
    if price is None:
        price = avg_cost
    return shares * price, shares * avg_cost


class Portfolio(commands.Cog):
    """Holdings, P&L, and rankings."""

    def __init__(self, bot):
        self.bot = bot
        self.last_posted = None  # date of the last weekly leaderboard
        self.weekly_leaderboard.start()

    def cog_unload(self):
        self.weekly_leaderboard.cancel()

    async def totals_by_user(self, user_ids=None) -> dict:
        """{user_id: (cash, market_value, cost_basis)} for everyone, or a subset."""
        rows = await db.all_users_with_holdings()

        # One row per holding, so cash repeats; collect it once per user.
        users = {}
        for user_id, cash, symbol, shares, avg_cost in rows:
            if user_ids is not None and user_id not in user_ids:
                continue
            entry = users.setdefault(user_id, {"cash": cash, "holdings": []})
            if symbol is not None:
                entry["holdings"].append((symbol, shares, avg_cost))

        symbols = {s for e in users.values() for s, _, _ in e["holdings"]}
        prices = await market.get_prices(symbols) if symbols else {}

        totals = {}
        for user_id, entry in users.items():
            value = cost = 0.0
            for symbol, shares, avg_cost in entry["holdings"]:
                position, basis = value_of(shares, avg_cost, prices.get(symbol))
                value += position
                cost += basis
            totals[user_id] = (entry["cash"], value, cost)
        return totals

    @commands.command(name="portfolio")
    async def portfolio(self, ctx, member: discord.Member = None):
        """Show cash, holdings, market value, and unrealized P&L."""
        target = member or ctx.author

        user = await db.get_user(target.id)
        if user is None:
            who = "They don't" if member else "You don't"
            await ctx.send(f"{who} have an account yet — `{config.COMMAND_PREFIX}start` opens one.")
            return

        cash = user[1]
        holdings = await db.get_holdings(target.id)
        prices = await market.get_prices([row[1] for row in holdings]) if holdings else {}

        lines = []
        value = cost = 0.0
        for _, symbol, shares, avg_cost in holdings:
            price = prices.get(symbol)
            position, basis = value_of(shares, avg_cost, price)
            value += position
            cost += basis
            pnl = position - basis
            flag = "" if price is not None else " (stale)"
            lines.append(
                f"{symbol:<6} {shares:>8.2f} @ {money(avg_cost):>12}"
                f" -> {money(position):>12} ({pnl:+,.2f}){flag}"
            )

        total = cash + value
        pnl = value - cost
        pnl_pct = (pnl / cost * 100) if cost else 0.0

        embed = discord.Embed(
            title=f"{target.display_name}'s portfolio",
            color=config.EMBED_COLOR,
        )
        embed.add_field(name="Cash", value=money(cash))
        embed.add_field(name="Holdings value", value=money(value))
        embed.add_field(name="Total", value=money(total))
        embed.add_field(
            name="Unrealized P&L",
            value=f"{pnl:+,.2f} ({pnl_pct:+.2f}%)" if cost else "—",
            inline=False,
        )
        if lines:
            embed.add_field(name="Positions", value="```\n" + "\n".join(lines) + "\n```", inline=False)
        else:
            embed.add_field(
                name="Positions",
                value=f"None yet — try `{config.COMMAND_PREFIX}buy AAPL 5`.",
                inline=False,
            )
        await ctx.send(embed=embed)

    async def build_leaderboard(self, guild) -> discord.Embed:
        """Rank the members of `guild` who have accounts, richest first."""
        members = {member.id: member for member in guild.members}
        totals = await self.totals_by_user(set(members))

        ranked = sorted(
            ((members[uid], cash + value, value - cost) for uid, (cash, value, cost) in totals.items()),
            key=lambda row: row[1],
            reverse=True,
        )[: config.LEADERBOARD_TOP_N]

        embed = discord.Embed(
            title=f"{guild.name} leaderboard",
            color=config.EMBED_COLOR,
        )
        if not ranked:
            embed.description = f"Nobody has played yet — `{config.COMMAND_PREFIX}start` to join."
            return embed

        medals = ("1.", "2.", "3.")
        lines = []
        for place, (member, total, pnl) in enumerate(ranked):
            marker = medals[place] if place < len(medals) else f"{place + 1}."
            lines.append(f"{marker:<4} {member.display_name:<20} {money(total):>13}  ({pnl:+,.2f})")
        embed.description = "```\n" + "\n".join(lines) + "\n```"
        return embed

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """Rank users in this guild by total portfolio value."""
        if ctx.guild is None:
            await ctx.send("Leaderboards only work in a server, not in DMs.")
            return
        await ctx.send(embed=await self.build_leaderboard(ctx.guild))

    # --- Background task ---

    @tasks.loop(hours=1)
    async def weekly_leaderboard(self):
        """Post the leaderboard once a week per LEADERBOARD_DAY/HOUR."""
        if config.LEADERBOARD_CHANNEL_ID is None:
            return

        now = datetime.now()
        if now.weekday() != config.LEADERBOARD_DAY or now.hour != config.LEADERBOARD_HOUR:
            return
        if self.last_posted == now.date():
            return  # the loop ticks hourly; only post once per scheduled day

        channel = self.bot.get_channel(config.LEADERBOARD_CHANNEL_ID)
        if channel is None or channel.guild is None:
            return

        embed = await self.build_leaderboard(channel.guild)
        embed.title = f"Weekly standings — {channel.guild.name}"
        await channel.send(embed=embed)
        self.last_posted = now.date()

    @weekly_leaderboard.before_loop
    async def before_weekly_leaderboard(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    """discord.py extension hook."""
    await bot.add_cog(Portfolio(bot))
