from discord.ext import commands
from discord.ext import tasks
import discord
import constants
import importlib
import random
import datetime
import time
import asyncio
import copy

trueskill_module = importlib.import_module('trueskill_automate')

class QueueCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.players_in_queue = []
    self.players_in_game = []
    self.games_in_progress = []
    self.games_in_progress_chk = 0
    self.last_ping_queue_nonempty = datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=3)
    self.QUEUE_MSG_ID = 0

  @commands.Cog.listener()
  async def on_ready(self):
      print(f"{self.__class__.__name__} loaded!")
      await self.send_init_q_msg()
      if not self.games_queue_logging.is_running():
          self.games_queue_logging.start()
      if not self.queue_printer.is_running():
          self.queue_printer.start()
      if not self.queue_limit_kicker.is_running():
          self.queue_limit_kicker.start()

  async def send_init_q_msg(self,):
      channel = self.bot.get_channel(constants.QUEUE_CHANNEL_ID)
      async for msg in channel.history(limit=2, oldest_first=False):
          if msg.content.startswith("**Current players") or msg.content.startswith("**GET IN HERE"):
              await msg.delete()
      msg = await channel.send(content="**Current players in queue:** \n")
      self.QUEUE_MSG_ID = msg.id

  async def initiate_queue_pop(self, players_list):
      channel = self.bot.get_channel(constants.MAIN_CHANNEL_ID)
      pop_msg = "Queue has popped for the following players: \n**Team1:**\n**---------------**\n"
      pop_msg_1 = "\n**Team2:**\n**---------------**\n"
      pop_msg_end = "\n If a player isn't here, use /clear_game."
      random.shuffle(players_list)
      count = 0
      for player_lis in players_list:
          if count < 4:
              pop_msg += f"<@{player_lis["discord_id"]}> "
          else:
              pop_msg_1 += f"<@{player_lis["discord_id"]}> "
          count += 1
      pop_msg+=pop_msg_1+pop_msg_end

      if len(self.players_in_queue) == 8:
          self.players_in_queue = []
      else:
          self.players_in_queue = [self.players_in_queue[i] for i in range(8, len(self.players_in_queue))]
      self.players_in_game += players_list
      self.games_in_progress.append(players_list)

      await channel.send(content=pop_msg)

  def check_if_qg(self, discord_name):
      exists = False
      for p_info in self.players_in_queue:
          if p_info["discord_name"] == discord_name:
              exists = True
      for p_lis in self.games_in_progress:
          for p_info in p_lis:
              if p_info["discord_name"] == discord_name:
                  exists = True
      return exists

  async def check_queue(self, ):
      if len(self.players_in_queue) >= 8:
          await self.initiate_queue_pop([self.players_in_queue[i] for i in range(8)])

  @commands.command(name="queue", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def queue(self, ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      
      if self.check_if_qg(ctx.author.name):
          await ctx.reply(f"You're already in queue or in game.", ephemeral=True)
          return
      player_dict = trueskill_module.get_player_pair_from_discord(ctx.author.name)
      if type(player_dict) is str:
          await ctx.reply(player_dict, ephemeral=True)
          return
      
      channel = self.bot.get_channel(constants.QUEUE_CHANNEL_ID)
      curr_time = datetime.datetime.now(datetime.timezone.utc)
      diff_time = (curr_time - self.last_ping_queue_nonempty).total_seconds()
      if not self.players_in_queue and diff_time>constants.PING_QNE_COOLDOWN:
          async for msg in channel.history(limit=2, oldest_first=False):
              if msg.content.startswith("**GET IN HERE"):
                  await msg.delete()
          await channel.send(content=f"**GET IN HERE!** 🔥🔥🔥 A player has queued up! RANKED QUEUE OPEN! <@&{constants.CUSTOMS_ROLE_ID}>")
          self.last_ping_queue_nonempty = curr_time

      player_dict.update({"discord_name":ctx.author.name})
      player_dict.update({"discord_id":ctx.author.id})
      player_dict.update({"min_since":0})

      self.players_in_queue.append(player_dict)
      await self.check_queue()
      
      await ctx.reply(f"Queued up {ctx.author.name}.", ephemeral=True)

  @commands.command(name="leave_queue", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def leave_queue(self, ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

      for player_info in self.players_in_queue:
          if player_info["discord_id"] == ctx.author.id:
              self.players_in_queue.remove(player_info)
              await ctx.reply(f"Removed {ctx.author.name} from queue.", ephemeral=True)
              return
      for player_info in self.players_in_game:
          if player_info["discord_id"] == ctx.author.id:
              self.players_in_game.remove(player_info)
              await ctx.reply(f"Removed {ctx.author.name} from queue.", ephemeral=True)
              return
      await ctx.reply(f"{ctx.author.name} not in queue.", ephemeral=True)

  @commands.command(name="clear_game", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def clear_game(self, ctx, discord_name: str=""):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

      name_chk = ctx.author.name if discord_name == "" else discord_name

      for game in self.games_in_progress:
          for player in game:
              if player["discord_name"] == name_chk:
                  self.games_in_progress.remove(game)
                  await ctx.reply(f"Removed game including {name_chk}. Please queue up again.")
                  return
      await ctx.reply(f"{name_chk} is not in a game.")

  @commands.command(name="get_games_in_progress", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def get_games_in_progress(self, ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      to_print = "**Current matches in progress:** \n"
      for g_info in self.games_in_progress:
          for p_info in g_info:
              to_print += f"{str(p_info["unique_name"])} - "
          to_print += "**---------------**\n\n"
      await ctx.reply(to_print)

  async def get_queue_print(self, ):
      to_print = "**Current players in queue:** \n"
      for p_info in self.players_in_queue:
          to_print += f"{str(p_info["unique_name"])} - "
      return to_print

  @commands.command(name="get_queue", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def get_queue(self, ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      to_print = await self.get_queue_print()
      await ctx.reply(to_print)

  async def game_end(self, game_index):
      for player_info in self.games_in_progress[game_index]:
          if player_info in self.players_in_game:
              self.players_in_queue.append(player_info)
              self.players_in_game.remove(player_info)
      self.games_in_progress.pop(game_index)

  @tasks.loop(minutes=1)
  async def queue_limit_kicker(self, ):
      #trueskill_module.log_stuff(f"\nPlayers curr in queue: -- {players_in_queue} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      channel = self.bot.get_channel(constants.MAIN_CHANNEL_ID)

      queuers_to_remove = []
      for i, p_info in enumerate(self.players_in_queue):
          if p_info["min_since"] >=60:
              trueskill_module.log_stuff(f"\nRemoving {p_info["unique_name"]} from queue for hitting 1 hour  --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
              await channel.send(content=f"<@{p_info["discord_id"]}> removed from queue (hour time limit).")
              queuers_to_remove.append(p_info)
              continue
          p_info["min_since"] += 1
          self.players_in_queue[i] = p_info
      for p in queuers_to_remove:
          self.players_in_queue.remove(p)
      if not self.players_in_queue:
          channel = self.bot.get_channel(constants.QUEUE_CHANNEL_ID)
          async for msg in channel.history(limit=2, oldest_first=False):
              if msg.content.startswith("**GET IN HERE"):
                  await msg.delete()

  @tasks.loop(seconds=20)
  async def games_queue_logging(self, ):
      channel = self.bot.get_channel(constants.MAIN_CHANNEL_ID)

      if self.games_in_progress == []:
          return
      trueskill_module.log_stuff(f"\nGoing through games IN PROGRESS queue -- {self.games_in_progress} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      
      i = 0
      while i < len(self.games_in_progress):
          p_lis = self.games_in_progress[i]
          p_lis_for_chcker = []
          for p_info in p_lis:
              p_lis_for_chcker.append(p_info["unique_name"])
          
          p_info = p_lis[games_in_progress_chk]
              
          trueskill_module.log_stuff(f"\nAttempting log queue entry {p_info["unique_name"]} (in-game)  --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
          return_str = await self.log_recent_game_standalone(p_info["unique_name"], p_lis_for_chcker)
          if not (return_str == None):
              await channel.send(content=return_str)
              i=0
              await self.game_end(i)
              await self.check_queue()
              break   
          await asyncio.sleep(1)
          i+=1
      games_in_progress_chk += 1
      if games_in_progress_chk == 8:
          games_in_progress_chk = 0

  @tasks.loop(seconds=20)
  async def queue_printer(self, ):
      msg = self.bot.get_message(self.QUEUE_MSG_ID)
      await msg.edit(content=await self.get_queue_print())

  @commands.command(name="randomize_teams", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def randomize_teams(self,ctx):
      async def contains(p_lis, filter):
          for x in p_lis:
              if filter(x):
                  return True
          return False 

      team_list = []
      for g_info in self.games_in_progress:
          if await contains(g_info, lambda x: x["discord_name"] == ctx.author.name):
              team_list = copy.deepcopy(g_info)
              random.shuffle(team_list)
              break
      pop_msg = "**Team1:**\n**---------------**\n"
      pop_msg_1 = "\n**Team2:**\n**---------------**\n"
      pop_msg_end = "\n If a player isn't here, use /clear_game."
      count = 0
      for player_lis in team_list:
          if count < 4:
              pop_msg += f"<@{player_lis["discord_id"]}> "
          else:
              pop_msg_1 += f"<@{player_lis["discord_id"]}> "
          count += 1
      pop_msg+=pop_msg_1+pop_msg_end
      await ctx.reply(pop_msg)


def setup(bot):
   bot.add_cog(QueueCog(bot))