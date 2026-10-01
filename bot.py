"""Entry point: loads the token, starts the bot, loads cogs."""
import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
from services.db import init_db

COGS = (
    "cogs.trading",
    "cogs.portfolio",
)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


async def load_cogs(bot):
    """Load every cog in COGS."""
    for cog in COGS:
        await bot.load_extension(cog)


async def main():
    """Init the DB, load cogs, start the bot with DISCORD_TOKEN."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

    await init_db()
    async with bot:
        await load_cogs(bot)
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
