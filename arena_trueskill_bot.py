import asyncio
import discord
import logging
from discord.ext import commands
import os
from dotenv import load_dotenv
from slash_commands.admin_commands import AdminCog
from slash_commands.bang_commands import BangCommandsCog
from slash_commands.logging_commands import LoggingCog
from slash_commands.player_commands import PlayerCog
from slash_commands.queue_commands import QueueCog
from slash_commands.testing_commands import TestsCog

# unused?
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents,
                   case_insensitive=False,)

async def on_ready():
    await bot.add_cog(TestsCog(bot))
    await bot.add_cog(QueueCog(bot))
    await bot.add_cog(PlayerCog(bot))
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(LoggingCog(bot))
    await bot.add_cog(BangCommandsCog(bot))
    print(bot.cogs.keys())

async def main():
    load_dotenv()
    async with bot:
      await on_ready()
      await bot.start(os.getenv("BOT_KEY"))
      print(f'Logged in as {bot.user}')

asyncio.run(main())
