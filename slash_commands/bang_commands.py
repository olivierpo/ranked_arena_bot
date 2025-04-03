from discord.ext import commands
from discord.ext import tasks
import discord
import constants
import importlib

from utils.sort_players import get_sorted_players
trueskill_module = importlib.import_module('../trueskill_automate.py')

import time
import copy
from collections import defaultdict

class BangCommandsCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  def decorate_rank_change(old_sorted_players, sorted_players):
      nested_dict = lambda: defaultdict(nested_dict) # allow dict[a][b]
      rank_changes_dict = nested_dict()
      old_rank_dict = {player: (idx, old_mmr) for idx, (old_mmr, old_conf, player) in enumerate(old_sorted_players[:19], start=1)}
      for new_idx, (new_mmr, new_conf, player) in enumerate(sorted_players[:19], start=1):
          old_rank = old_rank_dict.get(player)
          if old_rank:
              old_idx, old_mmr = old_rank
              if old_idx > new_idx:
                rank_changes_dict[player]['rank_change'] = f'+{old_idx - new_idx}🆙️'
              # # highlighting rank down is kind of bm
              # if old_idx < new_idx:
              #   rank_changes_dict[player] = f'- {new_idx - old_idx} ⬇️'
              if old_mmr > new_mmr:
                rank_changes_dict[player]['mmr_change'] = f'(-{round(old_mmr - new_mmr)})'
              if old_mmr < new_mmr:
                rank_changes_dict[player]['mmr_change'] = f'(+{round(new_mmr - old_mmr)})'
          else:
              # new player
              rank_changes_dict[player]['rank_change'] = '(Welcome to the top 20!)'

      return rank_changes_dict


  def fill_next_recur(self, team1, team2, players_full):
      '''returns mean team elo confidence and teams'''
      #print(f"\nteams: {team1} --- {team2} --- {players_full}\n")
      if len(team1) == 4:
          if len(team2) == 4:
              average_team_1 = (team1[0][1] + team1[1][1] + team1[2][1] + team1[3][1])/4.0
              average_team_2 = (team2[0][1] + team2[1][1] + team2[2][1] + team2[3][1])/4.0
              delta = abs(average_team_2 - average_team_1)
              #print("got here\n")
              return [delta, team1, team2]
      #print(f"\nteams: {team1} --- {team2} --- {players_full}\n")
      
      dict_keys = list(players_full.keys()) # player ids
      #print(str(dict_keys)+ " " + str(len(dict_keys)) + "\n")
      best_result = []
      for i in range(len(dict_keys)):
          #print(f"\nteams: {team1} --- {team2} --- {players_full}\n")
          temp_team1 = copy.deepcopy(team1)
          temp_team2 = copy.deepcopy(team2)
          if len(team1) == 4:
              temp_team2.append([dict_keys[i], players_full[dict_keys[i]]])
          else:
              temp_team1.append([dict_keys[i], players_full[dict_keys[i]]])
          temp_players_full = copy.deepcopy(players_full)
          temp_players_full.pop(dict_keys[i])
          curr_result = self.fill_next_recur(temp_team1, temp_team2, temp_players_full)
          if not best_result:
              best_result = curr_result
          else:
              if curr_result[0] < best_result[0]:
                  best_result = curr_result
      return best_result

  def balance_teams(self, players_to_balance):
      balance_result = self.fill_next_recur([], [], players_to_balance)
      return [balance_result[1], balance_result[2]]
    
  @commands.Cog.listener()
  async def on_message(self, message):
      sorted_players = get_sorted_players()
      if message.author == self.bot.user:
          return
      if message.content.startswith('!hello'):
          trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
          await message.reply('Hello!', mention_author=True)
      if message.content.startswith('!leaderboard'):
          trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
          leaderboard_str = "```Name." +(" "*40) + "Rank.\n"
          i = 0
          counted = 0
          while counted < 20:
              if i >= len(sorted_players):
                  break

              if (sorted_players[i]["wins"] + sorted_players[i]["losses"]) > 10:
                  to_add = f"{counted+1}. {sorted_players[i]["unique_name"]}"
                  whitespace_count = 45 - len(to_add)
                  to_add += (" "*whitespace_count)
                  leaderboard_str += (to_add+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
                  counted += 1
              i += 1
          leaderboard_str += "```"

          await message.reply(leaderboard_str, mention_author=True)
      if message.content.startswith('!balance'):
          trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
          sorted_players = get_sorted_players()
          balance_player_list = message.content[9:].split(",")
          trueskill_module.log_stuff(f"\n{balance_player_list}")
          if len(balance_player_list) != 8:
              await message.reply("Incorrect usage of !balance", mention_author=True)
              return
          rep = await message.reply("Balancing teams....this can take a minute...", mention_author=True)
          dict_to_balance = {}
          for i in range(len(sorted_players)):
              if sorted_players[i]["unique_name"] in balance_player_list:
                  dict_to_balance[sorted_players[i]["unique_name"]] = sorted_players[i]["mmr"]
          
          [team1, team2] = self.balance_teams(dict_to_balance)
          average_1 = (team1[0][1]+team1[1][1]+team1[2][1]+team1[3][1])/4
          printable_1 = f"Team1 (MMR:{average_1:.2f}): "
          printable_1 += f"{team1[0][0]}, {team1[1][0]}, {team1[2][0]}, {team1[3][0]}\n"
          average_2 = (team2[0][1]+team2[1][1]+team2[2][1]+team2[3][1])/4
          printable_2 = f"Team2 (MMR:{average_2:.2f}): "
          printable_2 += f"{team2[0][0]}, {team2[1][0]}, {team2[2][0]}, {team2[3][0]}"

          printable_1+=printable_2
          await rep.edit(content=printable_1)
      if message.content.startswith("!commands"):
          trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
          command_printable = constants.COMMANDS_STRING
          await message.reply(command_printable, mention_author=True)

def setup(bot):
   bot.add_cog(BangCommandsCog(bot))
