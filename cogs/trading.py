"""Trading commands: !start, !buy, !sell, !price."""

import discord
from discord.ext import commands

import config
from services import db, market


def money(amount: float) -> str:
    """Format a number as $1,234.56."""
    return f"${amount:,.2f}"


def valid_symbol(symbol: str) -> bool:
    """Cheap sanity check before we bother yfinance."""
    if not symbol or len(symbol) > config.MAX_SYMBOL_LEN:
        return False
    return all(char.isalpha() or char in ".-" for char in symbol)


class Trading(commands.Cog):
    """Buying, selling, and quoting symbols."""

    def __init__(self, bot):
        self.bot = bot

    async def resolve_price(self, ctx, symbol: str):
        """Return (symbol, price), or (symbol, None) after explaining why not."""
        symbol = market.normalize(symbol)
        if not valid_symbol(symbol):
            await ctx.send(f"`{symbol}` doesn't look like a ticker.")
            return symbol, None
        try:
            return symbol, await market.get_price(symbol)
        except market.UnknownSymbol:
            await ctx.send(f"Couldn't find a price for `{symbol}`.")
            return symbol, None
        except Exception:
            await ctx.send("Market data is unavailable right now. Try again in a moment.")
            return symbol, None

    async def require_account(self, ctx):
        """Return the user row, or None after telling them to run !start."""
        user = await db.get_user(ctx.author.id)
        if user is None:
            await ctx.send(f"{ctx.author.mention} run `{config.COMMAND_PREFIX}start` first.")
        return user

    @commands.command(name="start")
    async def start(self, ctx):
        """Create the caller's account with STARTING_CASH."""
        if not await db.create_user(ctx.author.id):
            await ctx.send(
                f"{ctx.author.mention} you already have an account. "
                f"Try `{config.COMMAND_PREFIX}portfolio`."
            )
            return

        embed = discord.Embed(
            title="Account opened",
            description=f"You start with **{money(config.STARTING_CASH)}** in fake money.",
            color=config.EMBED_COLOR,
        )
        embed.add_field(
            name="Next",
            value=f"`{config.COMMAND_PREFIX}price AAPL` then `{config.COMMAND_PREFIX}buy AAPL 5`",
        )
        await ctx.send(embed=embed)

    @commands.command(name="price")
    async def price(self, ctx, symbol: str):
        """Show the latest cached/live price for a symbol."""
        symbol, price = await self.resolve_price(ctx, symbol)
        if price is None:
            return
        await ctx.send(f"**{symbol}** — {money(price)}")

    @commands.command(name="buy")
    async def buy(self, ctx, symbol: str, qty: int):
        """Buy qty shares at the live price if the user can afford it."""
        if qty <= 0:
            await ctx.send("Quantity has to be a positive whole number.")
            return

        user = await self.require_account(ctx)
        if user is None:
            return
        cash = user[1]

        symbol, price = await self.resolve_price(ctx, symbol)
        if price is None:
            return

        cost = price * qty
        if cost > cash:
            await ctx.send(
                f"Not enough cash. **{qty} {symbol}** costs {money(cost)}, "
                f"you have {money(cash)}."
            )
            return

        # Weighted average cost: blend the existing position with this purchase.
        holding = await db.get_holding(ctx.author.id, symbol)
        old_shares = holding[2] if holding else 0.0
        old_avg = holding[3] if holding else 0.0
        new_shares = old_shares + qty
        new_avg = (old_shares * old_avg + qty * price) / new_shares

        await db.update_cash(ctx.author.id, -cost)
        await db.upsert_holding(ctx.author.id, symbol, new_shares, new_avg)
        await db.log_trade(ctx.author.id, symbol, "BUY", qty, price)

        embed = discord.Embed(
            title=f"Bought {qty} {symbol}",
            description=f"at {money(price)} — total {money(cost)}",
            color=config.EMBED_COLOR,
        )
        embed.add_field(name="Position", value=f"{new_shares:g} @ {money(new_avg)} avg")
        embed.add_field(name="Cash left", value=money(cash - cost))
        await ctx.send(embed=embed)

    @commands.command(name="sell")
    async def sell(self, ctx, symbol: str, qty: int):
        """Sell qty shares at the live price if the user holds enough."""
        if qty <= 0:
            await ctx.send("Quantity has to be a positive whole number.")
            return

        user = await self.require_account(ctx)
        if user is None:
            return
        cash = user[1]

        symbol = market.normalize(symbol)
        holding = await db.get_holding(ctx.author.id, symbol)
        if holding is None:
            await ctx.send(f"You don't own any **{symbol}**.")
            return

        held_shares, avg_cost = holding[2], holding[3]
        if qty > held_shares:
            await ctx.send(f"You only hold **{held_shares:g} {symbol}**.")
            return

        symbol, price = await self.resolve_price(ctx, symbol)
        if price is None:
            return

        proceeds = price * qty
        realized = (price - avg_cost) * qty

        await db.update_cash(ctx.author.id, proceeds)
        # avg_cost is unchanged by a sale; only the share count moves.
        await db.upsert_holding(ctx.author.id, symbol, held_shares - qty, avg_cost)
        await db.log_trade(ctx.author.id, symbol, "SELL", qty, price)

        sign = "+" if realized >= 0 else "-"
        embed = discord.Embed(
            title=f"Sold {qty} {symbol}",
            description=f"at {money(price)} — total {money(proceeds)}",
            color=config.EMBED_COLOR,
        )
        embed.add_field(name="Realized P&L", value=f"{sign}{money(abs(realized))}")
        embed.add_field(name="Remaining", value=f"{held_shares - qty:g} {symbol}")
        embed.add_field(name="Cash", value=money(cash + proceeds))
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx, error):
        """Turn argument mistakes into help text instead of tracebacks."""
        prefix = config.COMMAND_PREFIX
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{prefix}{ctx.command.name} {ctx.command.signature}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument. Try `{prefix}buy AAPL 5`.")
        else:
            raise error


async def setup(bot):
    """discord.py extension hook."""
    await bot.add_cog(Trading(bot))
