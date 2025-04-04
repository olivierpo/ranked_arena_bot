from discord.ext import commands
from discord.ext import tasks
import discord
import constants
import importlib
trueskill_module = importlib.import_module('trueskill_automate')

import re
import time
from utils.load_in_admins import load_in_admins

class AdminCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  """@bot.slash_command(name="get_all_players", description="attaches json file", guild_ids=GUILD_IDS)
  async def get_all_players(ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      if ctx.author.id in global_admin_list:
          player_file = discord.File("./player_ids.json")
          await ctx.send(file=player_file, content="JSON file containing all players.")
      else:
          await ctx.reply("Unauthorized", ephemeral=True)"""

  """@bot.slash_command(name="get_all_matches", description="attaches json file", guild_ids=GUILD_IDS)
  async def get_all_matches(ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      if ctx.author.id in global_admin_list:
          player_file = discord.File("./match_ids.json")
          await ctx.send(file=player_file, content="JSON file containing all matches.")
      else:
          await ctx.reply("Unauthorized", ephemeral=True)"""

  @commands.command(name="appoint_admin", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def appoint_admin(self, ctx, admin_to_appoint):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      if ctx.author.id == 118201449392898052:
          with open("../admin_list.txt", "a") as readfile:
              readfile.write(admin_to_appoint+"\n")
          await ctx.reply("Admin appointed", ephemeral=True)
      else:
          await ctx.reply("Unauthorized", ephemeral=True)

  @commands.command(name="remove_admin", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def remove_admin(self, ctx, admin_to_remove):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      if ctx.author.id == 118201449392898052:
          admin_list = ""
          with open("../admin_list.txt", "r") as readfile:
              admin_list = readfile.read()
          find_index = admin_list.find(admin_to_remove)
          admin_list = admin_list[0:find_index]+admin_list[(find_index+len(admin_to_remove)+1):]
          with open("../admin_list.txt", "w") as readfile:
              readfile.write(admin_list)
          await ctx.reply("Admin deleted", ephemeral=True)
      else:
          await ctx.reply("Unauthorized", ephemeral=True)

  @commands.command(name="backup_id_files", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def backup_id_files(self, ctx):
      admins = load_in_admins()
      if ctx.author.id in admins:
          trueskill_module.make_backup()
          await ctx.reply("Backed up id files.", ephemeral = True)
      else:
          await ctx.reply("Unauthorized", ephemeral = True)

  @commands.command(name="replace_players", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def replace_players(self, ctx, player_id_json: discord.Attachment):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      admins = load_in_admins()
      if ctx.author.id in admins:
          await player_id_json.save(fp="./temp_saves/"+player_id_json.filename)
          trueskill_module.replace_pfile_from_file(player_id_json.filename)
          await ctx.reply("Done", ephemeral=True)
      else:
          await ctx.reply("Not for you", ephemeral=True)

  @commands.command(name="get_admins", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def get_admins(self, ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      admins = load_in_admins()
      if ctx.author.id in admins:
          await ctx.reply(admins, ephemeral=True)
      else:
          await ctx.reply("Unauthorized", ephemeral=True)

  @commands.command(name="add_player_admin", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def add_player_admin(self, ctx, player_name, player_mmr=constants.MMR_DEFAULT, mmr_confidence=constants.CONFIDENCE_DEFAULT):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      admins = load_in_admins()
      if ctx.author.id in admins:
          pattern = re.compile("\\S+.*#\\S+")
          if not pattern.match(player_name):
              await ctx.reply("Inputted name not correct format", ephemeral=True)
              return
          #print(player_unique_name)
          user_id = self.get_id_from_name(player_name)
          
          if not user_id:
              await ctx.reply(f"Something went wrong", ephemeral=True)
              return
          #lp = soup.find("div", {"class": "lp"}).contents[0]

          #print(huge_string)
          #print(user_id)
          trueskill_module.add_player(user_id, player_name, mmr=player_mmr, sigma=mmr_confidence)
          await ctx.reply(f"Added {player_name} successfully", ephemeral=True)
      else:
          await ctx.reply(f"User not authorized", ephemeral=True)

  @commands.command(name="update_player", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def update_player(self, ctx, player_name: str, player_mmr=-1, mmr_confidence=-1):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      admins = load_in_admins()
      if ctx.author.id in admins:
          pattern = re.compile("\\S+.*#\\S+")
          if not pattern.match(player_name):
              await ctx.reply("Inputted name not correct format", ephemeral=True)
              return
          #print(player_unique_name)
          user_id = self.get_id_from_name(player_name)
          if not user_id:
              await ctx.reply(f"Something went wrong", ephemeral=True)
              return
          #lp = soup.find("div", {"class": "lp"}).contents[0]

          #print(huge_string)
          #print(user_id)
          error = trueskill_module.update_player(user_id, player_name, mmr=player_mmr, sigma=mmr_confidence)
          if error:
              await ctx.reply(error, ephemeral=True)
          await ctx.reply(f"Updated {player_name} successfully", ephemeral=True)
      else:
          await ctx.reply(f"User not authorized", ephemeral=True)

def setup(bot):
   bot.add_cog(AdminCog(bot))