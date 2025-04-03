from discord.ext import commands
from discord.ext import tasks
import discord
import constants
import importlib
trueskill_module = importlib.import_module('../trueskill_automate.py')

import time
import re
from utils.load_in_admins import load_in_admins

class LoggingCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  def get_teams_to_print(self,match_data):
      printable_team1 = "**Winners:**\n**---------------**\n"
      printable_team2 = "**Losers:**\n**---------------**\n"
      team1count = 1
      team2count = 5
      for i in range(len(match_data)):
          if match_data[i]["placement"] == 1:
              printable_team1 += f"{team1count}. " + match_data[i]["player"]["unique_display_name"] + "\n"
              team1count += 1
          if match_data[i]["placement"] == 2:
              printable_team2 += f"{team2count}. " + match_data[i]["player"]["unique_display_name"] + "\n"
              team2count += 1
      return printable_team1 + printable_team2

  @commands.command(name="log_recent_game", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def log_recent_game(self, ctx, player_name: discord.Option(str)):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      pattern = re.compile("\\S+.*#\\S+")
      if not pattern.match(player_name):
          await ctx.respond("Inputted name not correct format", ephemeral=True)
          return
      await ctx.respond("Loading...")
      match_details_return = await trueskill_module.check_match_w_name(player_name)
      if not match_details_return:
          trueskill_module.log_stuff(f"\n{match_id_return}")
          await ctx.edit(content=f"Could not log match for [error] reason")
          return
      if len(match_details_return) == 1:
          trueskill_module.log_stuff(f"\nlog returned 1 size")
          await ctx.edit(content=match_details_return[0])
          return
      match_id_return = match_details_return[1]
      
      
      #trueskill_module.log_stuff(f"\n{match_id_return}")
      #trueskill_module.log_stuff(f"\n{match_details_return[0]}")
      printed_content = f"Logged most recent match with id {match_id_return}\n" + self.get_teams_to_print(match_details_return[0])
      await ctx.edit(content=printed_content)

  @commands.command(name="log_specific_game", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def log_specific_game(self, ctx, match_id: discord.Option(str)):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      await ctx.respond("Loading...")
      match_details_return = await trueskill_module.check_new_match(match_id)
      if not match_details_return:
          trueskill_module.log_stuff(f"\n{match_id_return}")
          await ctx.edit(content=f"Could not log match")
          return
      if len(match_details_return) == 1:
          trueskill_module.log_stuff(f"\nlog returned 1 size")
          await ctx.edit(content=match_details_return[0])
          return
      match_id_return = match_details_return[1]
      #43b8e0ae-119c-4631-b18e-346c4b367440
      #print(match_details_return[0])
      printed_content = f"Logged specific match with id {match_id}\n" + self.get_teams_to_print(match_details_return[0])

      await ctx.edit(content=printed_content)

  """@bot.slash_command(name="log_next_game", guild_ids=GUILD_IDS) # Create a slash command
  async def log_next_game(ctx, player_name: discord.Option(str)):
      global logging_queue
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      pattern = re.compile("\\S+.*#\\S+")
      if not pattern.match(player_name):
          await ctx.respond("Inputted name not correct format", ephemeral=True)
          return
      logging_queue.append({"player_name":player_name, "min_since":0})
      await ctx.respond(f"Will log next game for {player_name}")"""

  async def log_recent_game_standalone(self, player_name, player_lis=[]):

      match_details_return = await trueskill_module.check_match_w_name(player_name, player_lis)
      if not match_details_return:
          trueskill_module.log_stuff(f"\n Error in match getting process for {player_name} IN-GAME CHECKING")
          return 
      if len(match_details_return) == 1:
          trueskill_module.log_stuff(f"\n{match_details_return[0]} IN-GAME CHECKING")
          return 
      match_id_return = match_details_return[1]
      
      printed_content = f"Logged most recent match with id {match_id_return}\n" + self.get_teams_to_print(match_details_return[0])
      
      return printed_content

  """@tasks.loop(minutes=2)
  async def log_queue():
      global logging_queue
      
      trueskill_module.log_stuff(f"\nGoing through log queue -- {logging_queue} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      channel = bot.get_channel(MAIN_CHANNEL_ID)
      fetch_p_matches_in_q()
      i = 0
      while i < len(logging_queue):
          q_dict = logging_queue[i]
          if q_dict["min_since"] >=10:
              await channel.send(content=f"All matches already logged for {q_dict["player_name"]} in last 10 minutes.")
              logging_queue.pop(i)
              continue
          trueskill_module.log_stuff(f"\nAttempting log queue entry {q_dict["player_name"]} - {q_dict["min_since"]}min --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
          return_str = await log_recent_game_standalone(q_dict["player_name"])
          if not (return_str == None):
              await channel.send(content=return_str)
              logging_queue.pop(i)
          else:
              q_dict["min_since"] += 2
              logging_queue[i] = q_dict
              i+=1
          time.sleep(3)"""
          
  @commands.command(name="clear_log_queue", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def clear_log_queue(self, ctx):
      admins = load_in_admins()
      if ctx.author.id in admins:
          self.logging_queue = []
          await ctx.respond("Cleared the log.", ephemeral=True)
      else:
          await ctx.respond("Unauthorized", ephemeral = True)

  @commands.command(name="check_log_queue", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def check_log_queue(self, ctx):
      queue_to_print = ""
      for queued_dict in self.logging_queue:
          queue_to_print += str(queued_dict) + "\n"
      await ctx.respond(f"Current log:\n{queue_to_print}", ephemeral=True)

def setup(bot):
   bot.add_cog(LoggingCog(bot))