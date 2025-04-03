from discord.ext import commands
import constants
from utils.load_in_admins import load_in_admins
import importlib
import time

trueskill_module = importlib.import_module('../trueskill_automate.py')

class TestsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players_in_queue = []
        if constants.TESTING:
          """ players_in_queue = [{"discord_name":"tsunani",
                                "discord_id":"tsunani",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "Tsunani#nani",
                "min_since":0
            },
            {"discord_name":"olivethebrave1",
                                "discord_id":"jetskii",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "jetskii#9028",
                "min_since":0
            },{"discord_name":"olivethebrave1",
                                "discord_id":"gothcowboy",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "gothcowboy#Jack",
                "min_since":0
            },{"discord_name":"olivethebrave1",
                                "discord_id":"Claire",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "Claire#6892",
                "min_since":0
            },{"discord_name":"olivethebrave1",
                                "discord_id":"trifox",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "trifox#5917",
                "min_since":0
            },{"discord_name":"olivethebrave1",
                                "discord_id":"Aposl",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "Aposl#VGBC",
                "min_since":0
            }]"""
        """,{"discord_name":"olivethebrave1",
                                "discord_id":"amatsuka",
                "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
                "unique_name": "amatsuka#4022",
                "min_since":0
            }"""


    def testing_helper(self, author_name):
        self.players_in_queue
        player_dict = trueskill_module.get_player_pair_from_discord(author_name)
        
        player_dict.update({"discord_name":author_name})
        player_dict.update({"discord_id":"12345"})
        player_dict.update({"min_since":0})

        self.players_in_queue.append(player_dict)

    @commands.command(name="test_stuff", guild_ids=constants.GUILD_IDS) # Create a slash command
    async def test_stuff(self, ctx):
        trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        if ctx.author.id == 118201449392898052: 
            trueskill_module.register("blah", "Tsunani#nani")
            self.testing_helper("blah")
            trueskill_module.register("blah1", "mvches#mvmv")
            self.testing_helper("blah1")
            self.testing_helper("blah2")
            self.testing_helper("blah3")
            self.testing_helper("blah4")
            self.testing_helper("blah5")
            self.testing_helper("blah6")
            trueskill_module.register("blah2", "Krilo#NUTT")
            trueskill_module.register("blah3", "Despi#derp")
            trueskill_module.register("blah4", "Mitchp#0000")
            trueskill_module.register("blah5", "Stevenator#546")
            trueskill_module.register("blah6", "Matty#9999")
            print(self.players_in_queue)
            await ctx.respond("Done", ephemeral=True)
            await ctx.edit(content="done edited")
        else:
            await ctx.respond("Not for you", ephemeral=True)

    @commands.command(name="reset_players", guild_ids=constants.GUILD_IDS) # Create a slash command
    async def reset_players(self, ctx):
        admins = load_in_admins()
        trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        if ctx.author.id in admins:
            trueskill_module.reset_player_file()
            await ctx.respond("Done", ephemeral=True)
        else:
            await ctx.respond("Not for you", ephemeral=True)

    @commands.command(name="reset_matches", guild_ids=constants.GUILD_IDS) # Create a slash command
    async def reset_matches(self, ctx):
        admins = load_in_admins()
        trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        if ctx.author.id in admins:
            trueskill_module.reset_match_file()
            await ctx.respond("Done", ephemeral=True)
        else:
            await ctx.respond("Not for you", ephemeral=True)


def setup(bot):
    bot.add_cog(TestsCog(bot))
