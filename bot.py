"""Entry point: loads the token, starts the bot, loads cogs."""

# TODO: imports (asyncio, os, discord, discord.ext.commands, dotenv)

COGS = (
    "cogs.trading",
    "cogs.portfolio",
)


# TODO: build the bot (command_prefix from config, intents with message_content)


async def load_cogs(bot):
    """Load every cog in COGS."""
    # TODO
    ...


async def main():
    """Init the DB, load cogs, start the bot with DISCORD_TOKEN."""
    # TODO
    ...


if __name__ == "__main__":
    # TODO: asyncio.run(main())
    ...
