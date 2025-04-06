from discord.ext import commands

GUILD_IDS = [441714985425436701]

class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('MyCog loaded!')

    @commands.command(name="hello", guild_ids=GUILD_IDS)  # Create a slash command
    async def hello(self, ctx):
        await ctx.send('Hello!')


async def setup(bot):
    await bot.add_cog(MyCog(bot))

# add the commands to the bot by adding
# await bot.add_cog(MyCog(bot))
# to the bot's on_ready() event