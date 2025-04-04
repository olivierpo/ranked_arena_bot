import re
import time
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext import tasks
import discord
import urllib3
import constants
import importlib
from utils.load_in_admins import load_in_admins

trueskill_module = importlib.import_module('trueskill_automate')
from utils.sort_players import get_sorted_players

class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def button_callback(self, button, interaction):
        new_button_0 = button
        #print(new_button_0.view.children)
        new_button_1 = button.view.children[0]
        if new_button_1.label == "1":
            await interaction.response.edit_message(content=button.view.message.content, view=button.view)
            return
        new_button_2 = button.view.children[1]
        new_button_2.label = new_button_1.label

        starting_int = int(new_button_1.label) - 11
        sorted_players = get_sorted_players()
        leaderboard_str = ""
        for i in range(starting_int, starting_int+10):
            if i >= len(sorted_players):
                break
            leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i]["unique_name"]} --- "+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
        new_button_1.label = str(int(new_button_1.label)-10)
        new_button_0.view.children[0] = new_button_1
        new_button_0.view.children[1] = new_button_2
        #print(new_button_0.view.children)
        await interaction.response.edit_message(content=leaderboard_str, view=new_button_0.view)
        #self.refresh()
        #await interaction.response.send_message(, ephemeral=True) # Send a message when the button is clicked

    @discord.ui.button(label="11", style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def second_button_callback(self, button, interaction):
        sorted_players = get_sorted_players()
        new_button_0 = button
        #print(new_button_0.view.children)
        new_button_1 = button.view.children[0]
        new_button_2 = button.view.children[1]
        new_button_1.label = new_button_2.label

        starting_int = int(new_button_2.label) - 1
        leaderboard_str = ""
        for i in range(starting_int, starting_int+10):
            if i >= len(sorted_players):
                break
            leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i]["unique_name"]} --- "+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
        new_button_2.label = str(int(new_button_2.label)+10)
        new_button_0.view.children[0] = new_button_1
        new_button_0.view.children[1] = new_button_2
        #print(new_button_0.view.children)
        await interaction.response.edit_message(content=leaderboard_str, view=new_button_0.view)

class PlayerCog(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command(name="get_player", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def get_player(self, ctx, player_name: str):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      sorted_players = get_sorted_players()
      for i in range(len(sorted_players)):
          if player_name.lower() == sorted_players[i]["unique_name"].lower():
              printed_stats = f"Name:  **{player_name}**\nTier:  **{trueskill_module.get_pretty_print_from_mmr(sorted_players[i]["mmr"])}**\nRank:  **{i+1}**\n"
              printed_stats += f"Wins:  **{sorted_players[i]["wins"]}**\nLosses:  **{sorted_players[i]["losses"]}**\nKills:  **{sorted_players[i]["stats"]["kills"]}**\n"
              printed_stats += f"Deaths:  **{sorted_players[i]["stats"]["deaths"]}**\nAssists:  **{sorted_players[i]["stats"]["assists"]}**\nDamage Done:  **{sorted_players[i]["stats"]["damage_done"]}**\n"
              printed_stats += f"Damage Taken:  **{sorted_players[i]["stats"]["damage_taken"]}**\nHealing Done:  **{sorted_players[i]["stats"]["healing_done"]}**"
              await ctx.reply(printed_stats, ephemeral=True)
              return
          
      await ctx.reply(f"Player {player_name} not found", ephemeral=True)



  def get_id_from_name(self, unique_name):
      username_final = trueskill_module.get_urlsafe_name(unique_name)
      url = f"https://supervive.op.gg/players/steam-{username_final}"
      http = urllib3.PoolManager()
      response = http.request('GET', url, decode_content=True)
      if response.status != 200:
          print("Player not found")
          return
      reply = response.data

      soup = BeautifulSoup(reply, 'html.parser')
      huge_string = soup.find(id="app")
      id_index = str(huge_string).find("user_id")
      #print(id_index)
      display_index = str(huge_string).find("display_name")
      if id_index == -1:
          print("ID not found for inputted name")
          return
      user_id = str(huge_string)[id_index+10:display_index-3]
      return user_id

  @commands.command(name="add_player", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def add_player(self, ctx, player_name: str):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      player_mmr = constants.MMR_DEFAULT
      mmr_confidence = constants.CONFIDENCE_DEFAULT
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
      trueskill_module.add_player(user_id, player_name)
      await ctx.reply(f"Added {player_name} successfully", ephemeral=True)

  @commands.command(name="remove_player", description="attaches json file", guild_ids=constants.GUILD_IDS)
  async def remove_player(self, ctx, player_name: str):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      await ctx.defer(ephemeral=True)
      pattern = re.compile("\\S+.*#\\S+")
      if not pattern.match(player_name):
          await ctx.reply("Inputted name not correct format", ephemeral=True)
          return

      error = trueskill_module.remove_player_w_name(player_name)
      if error:
          trueskill_module.log_stuff(error)
          await ctx.reply(error, ephemeral=True)
          return
      await ctx.reply(f"Removed {player_name} successfully", ephemeral=True)

  @commands.command(name="get_players_list", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def get_players_list(self, ctx):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      sorted_players = get_sorted_players()
      leaderboard_str = ""
      #print(sorted_players)
      for i in range(10):
          if i >= len(sorted_players):
              break
          leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i]["unique_name"]} --- "+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
          

      await ctx.reply(leaderboard_str, view=MyView(), ephemeral=True) # Send a message with our View class that contains the button

  @commands.command(name="register", guild_ids=constants.GUILD_IDS) # Create a slash command
  async def register(self, ctx, player_name: str):
      trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} -- {player_name}" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
      await ctx.defer()
      error = trueskill_module.register(ctx.author.name, player_name)
      if error:
          await ctx.reply(error, ephemeral=True)
          return
      await ctx.reply(f"Registered {ctx.author.name} to {player_name}.", ephemeral=True)

def setup(bot):
   bot.add_cog(PlayerCog(bot))