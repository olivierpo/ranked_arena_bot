from collections import defaultdict
import discord
import logging
import json
from discord.ext import commands
from discord.ext import tasks
from bs4 import BeautifulSoup
import urllib3
import re
import importlib
import time
import copy
import os
import asyncio
import random
import datetime
import sys
from wcwidth import wcswidth
from dotenv import load_dotenv

##############################  TESTING VARIABLE ################################
TESTING = 1
if __name__ == "__main__":
    if len(sys.argv) > 1:
        TESTING = int(sys.argv[1])
print(TESTING)
    

#################################################################################


if TESTING:
    BOT_KEY = "TEST_BOT_KEY"
    GUILD_IDS=[168149897512484866]
    MAIN_CHANNEL_ID=1352030483076218920
    QUEUE_CHANNEL_ID=1352030483076218920
    CUSTOMS_ROLE_ID=1356809301301395537
    QUEUE_CAT_ID = 1357106979679768748
    
else:
    BOT_KEY = "OLIV_BOT_KEY"
    GUILD_IDS=[168149897512484866, 1313026440660385834]
    MAIN_CHANNEL_ID=1352484632884416542
    QUEUE_CHANNEL_ID=1356775280399880272
    QUEUE_CAT_ID = 1357104967944769666
    CUSTOMS_ROLE_ID = 1313633911154409564
trueskill_module = importlib.import_module("trueskill_automate")

QUEUE_MSG_ID = 0
MMR_DEFAULT = 1000
CONFIDENCE_DEFAULT = 333
PING_QNE_COOLDOWN = datetime.timedelta(hours=3).total_seconds()

COMMANDS_STRING = """
        **PUBLIC:**
        *<!leaderboard>* Prints leaderboard.
        *<!balance user_name1,username2,...username8>* Prints balanced teams from usernames. No spaces between names, just commas. 
        *</get_player user_name>* Prints player MMR, rank and stats.
        *</update_name user_name>* Updates player display name in all databases. Use if you just changed your name.
        *</register user_name>* Adds you to the ranked system.
        *</queue>* Put yourself in queue for a ranked game. Must be registered.
        *</leave_queue>* Leave queue. Will also work if you're in game so you don't auto-requeue.
        *</clear_game>* Clear the current popped game. Game's players must requeue.
        *</get_players_list>* Lets you read through all players sorted by rank.
        *</randomize_teams>* Performs a built-in randomize function on teams. Do it as many times as you want.

        *</get_games_in_progress>* Get list of all games currently in progress.
        *</get_queue>* Get list of all players currently in queue.

        If the game fails to log due to a name issue, get an admin to get the match_id.
        *</log_specific_game match_id>* Rates specific game IF the game is an arena custom game and ALL PLAYERS are in the system.
        

        ***All usernames are CASE SENSITIVE. Please double check!***
        """

intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(command_prefix="/", intents=intents,
                   case_insensitive=False,)

players_in_memory = ""
sorted_players = []
global_admin_list = []
logging_queue = []

players_in_queue = []
players_in_game = []
games_in_progress = []
games_in_progress_chk = 0
prev_len = 0

last_ping_queue_nonempty = datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=3)

if TESTING:
    players_in_queue = [{"discord_name":"tsunani",
                         "discord_id":"tsunani",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "Lucidious#0000",
        "min_since":0
    },
    {"discord_name":"olivethebrave1",
                         "discord_id":"jetskii",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "BoredLoser#6969",
        "min_since":0
    },{"discord_name":"olivethebrave1",
                         "discord_id":"gothcowboy",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "shmovement#0000",
        "min_since":0
    },{"discord_name":"olivethebrave1",
                         "discord_id":"Claire",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "polts#2002",
        "min_since":0
    },{"discord_name":"olivethebrave1",
                         "discord_id":"trifox",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "trifox#5917",
        "min_since":0
    },{"discord_name":"olivethebrave1",
                         "discord_id":"Aposl",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "crownella#1420",
        "min_since":0
    }
,{"discord_name":"olivethebrave1",
                         "discord_id":"amatsuka",
        "ingame_id": "3131248f6e5a4c64a1a9664135978d95",
        "unique_name": "Geb#1087",
        "min_since":0
    }]

def load_in_admins():
    """
    Load in the list of administrators from a file.
    """
    global global_admin_list
    global_admin_list = [118201449392898052, 242753760890191884]
    with open("admin_list.txt", "r") as readfile:
        for admins in readfile:
            global_admin_list.append(int(admins[:-1]))

def get_players():
    '''
    assigns all registered player ids to global variable `players_in_memory` 
    '''
    global players_in_memory
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    players_in_memory = to_read
    return to_read

def p1_is_worse(player1, player2):
    if player1["mmr"] < player2["mmr"]:
        return 1
    else:
        return 0
    


def get_sorted_players():
    '''
    ranks players by elo (highest to lowest) using bubble sort

    creates new global variable `sorted_players`

    `[[250, 100, "Player1Name#ID"], [200, 100, "Player2Name#ID"]]`
    '''
    global sorted_players
    global players_in_memory
    players_list = list(players_in_memory.values())
    for i in range(len(players_in_memory.keys())):
        for j in range(len(players_in_memory.keys())):
            if i == j:
                continue
            p1 = players_list[i]
            p2 = players_list[j]
            if p1_is_worse(p1, p2):
                continue
            else:
                players_list[i] = p2
                players_list[j] = p1

    sorted_players = players_list
    

class MyView(discord.ui.View): 
    """
    Create a custom view class for a Discord bot interface.
    This class will inherit from discord.ui.View.
    """
    @discord.ui.button(label="1", style=discord.ButtonStyle.primary, emoji="😎") 
    async def button_callback(self, button, interaction):
        """
        Define a button with label "1", primary style, and emoji "😎" for a Discord UI.
        @param label - The text displayed on the button.
        @param style - The visual style of the button.
        @param emoji - The emoji displayed on the button.
        @return An asynchronous callback function for the button interaction.
        """
        new_button_0 = button

        new_button_1 = button.view.children[0]
        if new_button_1.label == "1":
            await interaction.response.edit_message(content=button.view.message.content, view=button.view)
            return
        new_button_2 = button.view.children[1]
        new_button_2.label = new_button_1.label

        starting_int = int(new_button_1.label) - 11
        global sorted_players
        leaderboard_str = ""
        for i in range(starting_int, starting_int+10):
            if i >= len(sorted_players):
                break
            leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i]["unique_name"]} --- "+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
        new_button_1.label = str(int(new_button_1.label)-10)
        new_button_0.view.children[0] = new_button_1
        new_button_0.view.children[1] = new_button_2

        await interaction.response.edit_message(content=leaderboard_str, view=new_button_0.view)


    @discord.ui.button(label="11", style=discord.ButtonStyle.primary, emoji="😎") 
    async def second_button_callback(self, button, interaction):
        """
        Define an asynchronous callback function for the second button in the user interface.
        @param self - the class instance
        @param button - the second button in the UI
        @param interaction - the user interaction event
        @return None
        """
        global sorted_players
        new_button_0 = button

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

        await interaction.response.edit_message(content=leaderboard_str, view=new_button_0.view)

def fill_next_recur(team1, team2, players_full):
    """
    This function recursively fills two teams with players from a dictionary to minimize the difference in average team elo confidence.
    @param team1 - the first team being filled
    @param team2 - the second team being filled
    @param players_full - a dictionary of players and their elo confidence
    @return A list containing the difference in average team elo confidence and the two teams with players assigned to them.
    """

    if len(team1) == 4:
        if len(team2) == 4:
            average_team_1 = (team1[0][1] + team1[1][1] + team1[2][1] + team1[3][1])/4.0
            average_team_2 = (team2[0][1] + team2[1][1] + team2[2][1] + team2[3][1])/4.0
            delta = abs(average_team_2 - average_team_1)

            return [delta, team1, team2]

    
    dict_keys = list(players_full.keys()) # player ids

    best_result = []
    for i in range(len(dict_keys)):

        temp_team1 = copy.deepcopy(team1)
        temp_team2 = copy.deepcopy(team2)
        if len(team1) == 4:
            temp_team2.append([dict_keys[i], players_full[dict_keys[i]]])
        else:
            temp_team1.append([dict_keys[i], players_full[dict_keys[i]]])
        temp_players_full = copy.deepcopy(players_full)
        temp_players_full.pop(dict_keys[i])
        curr_result = fill_next_recur(temp_team1, temp_team2, temp_players_full)
        if not best_result:
            best_result = curr_result
        else:
            if curr_result[0] < best_result[0]:
                best_result = curr_result
    return best_result

def balance_teams(players_to_balance):
    """
    Balance the teams by recursively filling the next team until all players are assigned.
    @param players_to_balance - list of players to be balanced into teams
    @return A list containing the balanced teams.
    """
    balance_result = fill_next_recur([], [], players_to_balance)
    return [balance_result[1], balance_result[2]]
    
def decorate_rank_change(old_sorted_players, sorted_players):
    """
    I don't remember why I made this.
    @param old_sorted_players - The list of players with their old ranks and MMRs.
    @param sorted_players - The list of players with their new ranks and MMRs.
    @return A nested dictionary containing the rank and MMR changes for each player.
    """
    nested_dict = lambda: defaultdict(nested_dict) # allow dict[a][b]
    rank_changes_dict = nested_dict()
    old_rank_dict = {player: (idx, old_mmr) for idx, (old_mmr, old_conf, player) in enumerate(old_sorted_players[:19], start=1)}
    for new_idx, (new_mmr, new_conf, player) in enumerate(sorted_players[:19], start=1):
        old_rank = old_rank_dict.get(player)
        if old_rank:
            old_idx, old_mmr = old_rank
            if old_idx > new_idx:
              rank_changes_dict[player]['rank_change'] = f'+{old_idx - new_idx}🆙️'

            if old_mmr > new_mmr:
              rank_changes_dict[player]['mmr_change'] = f'(-{round(old_mmr - new_mmr)})'
            if old_mmr < new_mmr:
              rank_changes_dict[player]['mmr_change'] = f'(+{round(new_mmr - old_mmr)})'
        else:

            rank_changes_dict[player]['rank_change'] = '(Welcome to the top 20!)'

    return rank_changes_dict


@bot.event
async def on_message(message):
    """
    Handle different message commands in an asynchronous manner.
    @param message - the message received
    @return None
    """
    global sorted_players
    if message.author == bot.user:
        return
    if message.content.startswith('!hello'):
        trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        await message.reply('Hello!', mention_author=True)
    if message.content.startswith('!leaderboard'):
        trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

        old_sorted_players = copy.deepcopy(sorted_players)

        get_players()
        get_sorted_players()

        leaderboard_str = "```Name." +(" "*40) + "Rank.\n"


        i = 0
        counted = 0
        while counted < 20:
            if i >= len(sorted_players):
                break

            if (sorted_players[i]["wins"] + sorted_players[i]["losses"]) > 10:
                to_add = f"{counted+1}. {sorted_players[i]["unique_name"]}"
                whitespace_count = 45 - wcswidth(to_add)
                to_add += (" "*whitespace_count)
                leaderboard_str += (to_add+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
                counted += 1
            i += 1
        leaderboard_str += "```"

        await message.reply(leaderboard_str, mention_author=True)
    if message.content.startswith('!balance'):
        trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        get_players()
        get_sorted_players()
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
        
        [team1, team2] = balance_teams(dict_to_balance)
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
        command_printable = COMMANDS_STRING
        await message.reply(command_printable, mention_author=True)
    

@bot.slash_command(name="appoint_admin", description="attaches json file", guild_ids=GUILD_IDS)
async def appoint_admin(ctx, admin_to_appoint: discord.Option(str)):
    """Appoint a new admin (owner only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id == 118201449392898052:
        with open("admin_list.txt", "a") as readfile:
            readfile.write(admin_to_appoint+"\n")
        load_in_admins()
        await ctx.respond("Admin appointed", ephemeral=True)
    else:
        await ctx.respond("Unauthorized", ephemeral=True)

@bot.slash_command(name="remove_admin", description="attaches json file", guild_ids=GUILD_IDS)
async def remove_admin(ctx, admin_to_remove: discord.Option(str)):
    """Remove an admin (owner only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id == 118201449392898052:
        admin_list = ""
        with open("admin_list.txt", "r") as readfile:
            admin_list = readfile.read()
        find_index = admin_list.find(admin_to_remove)
        admin_list = admin_list[0:find_index]+admin_list[(find_index+len(admin_to_remove)+1):]
        with open("admin_list.txt", "w") as readfile:
            readfile.write(admin_list)
        load_in_admins()
        await ctx.respond("Admin deleted", ephemeral=True)
    else:
        await ctx.respond("Unauthorized", ephemeral=True)

@bot.slash_command(name="get_admins", description="attaches json file", guild_ids=GUILD_IDS)
async def get_admins(ctx):
    """Show current admin IDs (admin only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global global_admin_list
    if ctx.author.id in global_admin_list:
        await ctx.respond(global_admin_list, ephemeral=True)
    else:
        await ctx.respond("Unauthorized", ephemeral=True)



@bot.slash_command(name="get_player", description="attaches json file", guild_ids=GUILD_IDS)
async def get_player(ctx, player_name: discord.Option(str)):
    """Show a player's MMR, rank, and stats."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global sorted_players
    get_players()
    get_sorted_players()
    for i in range(len(sorted_players)):
        if player_name.lower() == sorted_players[i]["unique_name"].lower():
            printed_stats = f"Name:  **{player_name}**\nTier:  **{trueskill_module.get_pretty_print_from_mmr(sorted_players[i]["mmr"])}**\nRank:  **{i+1}**\n"
            printed_stats += f"Wins:  **{sorted_players[i]["wins"]}**\nLosses:  **{sorted_players[i]["losses"]}**\nKills:  **{sorted_players[i]["stats"]["kills"]}**\n"
            printed_stats += f"Deaths:  **{sorted_players[i]["stats"]["deaths"]}**\nAssists:  **{sorted_players[i]["stats"]["assists"]}**\nDamage Done:  **{sorted_players[i]["stats"]["damage_done"]}**\n"
            printed_stats += f"Damage Taken:  **{sorted_players[i]["stats"]["damage_taken"]}**\nHealing Done:  **{sorted_players[i]["stats"]["healing_done"]}**"
            await ctx.respond(printed_stats, ephemeral=True)
            return
        
    await ctx.respond(f"Player {player_name} not found", ephemeral=True)



def get_id_from_name(unique_name):
    """
    Retrieve the user ID from a unique name by accessing an op.gg URL and parsing the HTML content using soup.
    @param unique_name - the unique name of the user
    @return The user ID
    """
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

    display_index = str(huge_string).find("display_name")
    if id_index == -1:
        print("ID not found for inputted name")
        return
    user_id = str(huge_string)[id_index+20:display_index-13]
    return user_id

@bot.slash_command(name="add_player_admin", description="attaches json file", guild_ids=GUILD_IDS)
async def add_player_admin(ctx, player_name: discord.Option(str), player_mmr: discord.Option(float, required = False, default=MMR_DEFAULT), mmr_confidence: discord.Option(float, required = False, default=CONFIDENCE_DEFAULT)):
    """Admin: add player with MMR and sigma."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        pattern = re.compile("\\S+.*#\\S+")
        if not pattern.match(player_name):
            await ctx.respond("Inputted name not correct format", ephemeral=True)
            return

        user_id = get_id_from_name(player_name)
        
        if not user_id:
             await ctx.respond(f"Something went wrong", ephemeral=True)
             return

        trueskill_module.add_player(user_id, player_name, mmr=player_mmr, sigma=mmr_confidence)
        await ctx.respond(f"Added {player_name} successfully", ephemeral=True)
    else:
        await ctx.respond(f"User not authorized", ephemeral=True)

@bot.slash_command(name="add_player", description="attaches json file", guild_ids=GUILD_IDS)
async def add_player(ctx, player_name: discord.Option(str)):
    """Add a player with default MMR and sigma."""
    await ctx.defer(ephemeral=True)
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    player_mmr = MMR_DEFAULT
    mmr_confidence = CONFIDENCE_DEFAULT
    pattern = re.compile("\\S+.*#\\S+")
    if not pattern.match(player_name):
        await ctx.respond("Inputted name not correct format", ephemeral=True)
        return

    user_id = get_id_from_name(player_name)
    
    if not user_id:
        await ctx.respond(f"Something went wrong", ephemeral=True)
        return

    trueskill_module.add_player(user_id, player_name)
    await ctx.send_followup(f"Added {player_name} successfully", ephemeral=True)

@bot.slash_command(name="remove_player", description="attaches json file", guild_ids=GUILD_IDS)
async def remove_player(ctx, player_name: discord.Option(str)):
    """Remove a player by unique name."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    await ctx.defer(ephemeral=True)
    pattern = re.compile("\\S+.*#\\S+")
    if not pattern.match(player_name):
        await ctx.send_followup("Inputted name not correct format", ephemeral=True)
        return

    error = trueskill_module.remove_player_w_name(player_name)
    if error:
        trueskill_module.log_stuff(error)
        await ctx.send_followup(error, ephemeral=True)
        return
    await ctx.send_followup(f"Removed {player_name} successfully", ephemeral=True)

@bot.slash_command(name="update_player", description="attaches json file", guild_ids=GUILD_IDS)
async def update_player(ctx, player_name: discord.Option(str), player_mmr: discord.Option(float, required = False, default=-1), mmr_confidence: discord.Option(float, required = False, default=-1)):
    """Admin: update a player's MMR and sigma."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    await ctx.defer(ephemeral=True)
    if ctx.author.id in global_admin_list:
        pattern = re.compile("\\S+.*#\\S+")
        if not pattern.match(player_name):
            await ctx.send_followup("Inputted name not correct format", ephemeral=True)
            return

        user_id = get_id_from_name(player_name)
        if not user_id:
             await ctx.send_followup(f"Something went wrong", ephemeral=True)
             return

        error = trueskill_module.update_player(user_id, player_name, mmr=player_mmr, sigma=mmr_confidence)
        if error:
            await ctx.send_followup(error, ephemeral=True)
        await ctx.send_followup(f"Updated {player_name} successfully", ephemeral=True)
    else:
        await ctx.send_followup(f"User not authorized", ephemeral=True)

def get_teams_to_print(match_data):
    """
    Generate a formatted list of winning and losing teams from the match data.
    @param match_data - the data containing match results
    @return A formatted string listing the winning and losing teams
    """
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


@bot.slash_command(name="log_recent_game", guild_ids=GUILD_IDS) # Create a slash command
async def log_recent_game(ctx, player_name: discord.Option(str)):
    """Log the most recent custom game for a player."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    pattern = re.compile("\\S+.*#\\S+")
    await ctx.defer()
    if not pattern.match(player_name):
        await ctx.send_followup("Inputted name not correct format", ephemeral=True)
        return
    
    match_details_return = await trueskill_module.check_match_w_name(player_name)
    if not match_details_return:
        trueskill_module.log_stuff(f"\n{match_id_return}")
        await ctx.send_followup(content=f"Could not log match for [error] reason")
        return
    if len(match_details_return) == 1:
        trueskill_module.log_stuff(f"\nlog returned 1 size")
        await ctx.send_followup(content=match_details_return[0])
        return
    match_id_return = match_details_return[1]
    
    
    #trueskill_module.log_stuff(f"\n{match_id_return}")
    #trueskill_module.log_stuff(f"\n{match_details_return[0]}")
    printed_content = f"Logged most recent match with id {match_id_return}\n" + get_teams_to_print(match_details_return[0])
    await ctx.edit(content=printed_content)

@bot.slash_command(name="log_specific_game", guild_ids=GUILD_IDS) # Create a slash command
async def log_specific_game(ctx, match_id: discord.Option(str)):
    """Log a specific custom game by match ID."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    await ctx.defer()
    match_details_return = await trueskill_module.check_new_match(match_id)
    if not match_details_return:
        trueskill_module.log_stuff(f"\n{match_id_return}")
        await ctx.send_followup(content=f"Could not log match")
        return
    if len(match_details_return) == 1:
        trueskill_module.log_stuff(f"\nlog returned 1 size")
        await ctx.send_followup(content=match_details_return[0])
        return
    match_id_return = match_details_return[1]
    printed_content = f"Logged specific match with id {match_id}\n" + get_teams_to_print(match_details_return[0])

    await ctx.send_followup(content=printed_content)


async def log_recent_game_standalone(player_name, player_lis=[]):
    """
    Asynchronously log the most recent game played by a player and return the match details.
    @param player_name - the name of the player
    @param player_lis - list of players in the match
    @return The printed content of the most recent match with its ID and team details.
    """

    match_details_return = await trueskill_module.check_match_w_name(player_name, player_lis)
    if not match_details_return:
        trueskill_module.log_stuff(f"\n Error in match getting process for {player_name} IN-GAME CHECKING")
        return 
    if len(match_details_return) == 1:
        trueskill_module.log_stuff(f"\n{match_details_return[0]} IN-GAME CHECKING")
        return 
    match_id_return = match_details_return[1]
    
    printed_content = f"Logged most recent match with id {match_id_return}\n" + get_teams_to_print(match_details_return[0])
    
    return printed_content


        
@bot.slash_command(name="clear_log_queue", guild_ids=GUILD_IDS) # Create a slash command
async def clear_log_queue(ctx):
    """Clear the logging queue (admin only)."""
    global logging_queue
    if ctx.author.id in global_admin_list:
        logging_queue = []
        await ctx.respond("Cleared the log.", ephemeral=True)
    else:
        await ctx.respond("Unauthorized", ephemeral = True)

@bot.slash_command(name="get_players_list", guild_ids=GUILD_IDS) # Create a slash command
async def get_players_list(ctx):
    """Show top 10 players and ranks."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global sorted_players
    get_players()
    get_sorted_players()
    leaderboard_str = ""
    #print(sorted_players)
    for i in range(10):
        if i >= len(sorted_players):
            break
        leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i]["unique_name"]} --- "+trueskill_module.get_pretty_print_from_mmr(int(sorted_players[i]["mmr"])) + "\n")
        

    await ctx.respond(leaderboard_str, view=MyView(), ephemeral=True) # Send a message with our View class that contains the button

@bot.slash_command(name="check_log_queue", guild_ids=GUILD_IDS) # Create a slash command
async def check_log_queue(ctx):
    """Show the current logging queue."""
    global logging_queue
    queue_to_print = ""
    for queued_dict in logging_queue:
        queue_to_print += str(queued_dict) + "\n"
    await ctx.respond(f"Current log:\n{queue_to_print}", ephemeral=True)


@bot.slash_command(name="backup_id_files", guild_ids=GUILD_IDS) # Create a slash command
async def backup_id_files(ctx):
    """Back up player and match ID files (admin only)."""
    if ctx.author.id in global_admin_list:
        trueskill_module.make_backup()
        await ctx.respond("Backed up id files.", ephemeral = True)
    else:
        await ctx.respond("Unauthorized", ephemeral = True)

@bot.slash_command(name="replace_players", guild_ids=GUILD_IDS) # Create a slash command
async def replace_players(ctx, player_id_json: discord.Attachment):
    """Replace player_ids.json from an attached file (admin only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        await player_id_json.save(fp="./temp_saves/"+player_id_json.filename)
        trueskill_module.replace_pfile_from_file(player_id_json.filename)
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)

@bot.slash_command(name="register", guild_ids=GUILD_IDS) # Create a slash command
async def register(ctx, player_name: discord.Option(str)):
    """Register your Discord user to a unique name."""
    await ctx.defer(ephemeral=True)
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} -- {player_name}" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    pattern = re.compile("\\S+.*#\\S+")
    if not pattern.match(player_name):
        await ctx.respond("Inputted name not correct format", ephemeral=True)
        return

    user_id = get_id_from_name(player_name)
    
    if not user_id:
        await ctx.respond(f"Something went wrong", ephemeral=True)
        return

    error = trueskill_module.add_player(user_id, player_name)
    if error:
        await ctx.send_followup(error, ephemeral=True)
        return
    
    error = trueskill_module.register(ctx.author.name, player_name)
    if error:
        await ctx.send_followup(error, ephemeral=True)
        return
    await ctx.send_followup(f"Registered {ctx.author.name} to {player_name}.", ephemeral=True)

async def contains(p_lis, filter):
    """
    Check if any element in the list satisfies the given filter condition asynchronously.
    @param p_lis - The list to be checked.
    @param filter - The filter condition to be applied.
    @return True if any element satisfies the filter condition, False otherwise.
    """
    for x in p_lis:
        if filter(x):
            return True
    return False 

@bot.slash_command(name="randomize_teams", guild_ids=GUILD_IDS) # Create a slash command
async def randomize_teams(ctx):
    """Randomly split your current game into teams."""
    await ctx.defer()
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name}" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global games_in_progress
    team_list = []
    for g_info in games_in_progress:
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
    await ctx.send_followup(pop_msg)


async def initiate_queue_pop(players_list):
    """
    Initiate the process of popping players from the queue to start a game.
    @param players_list - List of players in the queue
    @return None
    """
    global players_in_queue
    global games_in_progress
    global players_in_game
    channel = bot.get_channel(MAIN_CHANNEL_ID)
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

    if len(players_in_queue) == 8:
        players_in_queue = []
    else:
        players_in_queue = [players_in_queue[i] for i in range(8, len(players_in_queue))]
    players_in_game += players_list
    games_in_progress.append(players_list)

    await channel.send(content=pop_msg)

def check_if_qg(discord_name):
    """
    Check if a player with the given Discord name is in the queue or in a game in progress.
    @param discord_name - The Discord name of the player to check
    @return True if the player is in the queue or in a game in progress, False otherwise
    """
    global players_in_queue
    global games_in_progress
    exists = False
    for p_info in players_in_queue:
        if p_info["discord_name"] == discord_name:
            exists = True
    for p_lis in games_in_progress:
        for p_info in p_lis:
            if p_info["discord_name"] == discord_name:
                exists = True
    return exists

async def check_queue():
    """
    Asynchronously check the queue for the number of players in the queue. If there are 8 or more players in the queue, initiate the queue pop process with the first 8 players.
    @return None
    """
    global players_in_queue
    if len(players_in_queue) >= 8:
        await initiate_queue_pop([players_in_queue[i] for i in range(8)])

async def change_q_channel():
    """
    Asynchronously update the voice channel in a Discord server to reflect the number of players in the queue.
    @returns None
    """
    guild = bot.get_guild(GUILD_IDS[0 if TESTING else 1])
    category = bot.get_channel(QUEUE_CAT_ID)
    for vc in guild.voice_channels:
        if vc.name.startswith("🟢"):
            await vc.delete()
    await category.create_voice_channel(name=f"🟢-{len(players_in_queue)}-PLAYERS-IN-QUEUE")

# bot.close() not supported with bot.run(). Keyboard interrupt is intended shutdown
"""@bot.slash_command(name="shutdown", guild_ids=GUILD_IDS) # Create a slash command
async def shutdown(ctx):
    if ctx.author.id in global_admin_list:
        await ctx.respond("Shutting down...")
        await bot.close()
        if bot.http and hasattr(bot.http, "_HTTPClient__session"):
            await bot.http._HTTPClient__session.close()
    else:
        await ctx.respond("You do not have permission to shut down the bot. Contact an administrator.")"""


@bot.slash_command(name="update_name", guild_ids=GUILD_IDS) # Create a slash command
async def update_name(ctx, player_name: discord.Option(str)):
    """Update your stored unique name."""
    await ctx.defer(ephemeral=True)
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} -- {player_name}" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    player_dict = trueskill_module.get_player_pair_from_discord(ctx.author.name)
    if type(player_dict) is str:
        await ctx.send_followup(player_dict, ephemeral=True)
        return
    pattern = re.compile("\\S+.*#\\S+")
    if not pattern.match(player_name):
        await ctx.respond("Inputted name not correct format", ephemeral=True)
        return
    error = trueskill_module.fix_name_manual(player_name, player_dict["ingame_id"])
    if error:
        await ctx.send_followup(error, ephemeral=True)
        return
    await ctx.send_followup(f"Updated name for {ctx.author.name}.", ephemeral=True)

@bot.slash_command(name="queue", guild_ids=GUILD_IDS) # Create a slash command
async def queue(ctx):
    """Enter the ranked queue."""
    await ctx.defer(ephemeral=True)
    global players_in_queue
    global last_ping_queue_nonempty
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if check_if_qg(ctx.author.name):
        await ctx.send_followup(f"You're already in queue or in game.", ephemeral=True)
        return
    player_dict = trueskill_module.get_player_pair_from_discord(ctx.author.name)
    if type(player_dict) is str:
        await ctx.send_followup(player_dict, ephemeral=True)
        return
    
    #error = await trueskill_module.fix_name_from_ID(player_dict["ingame_id"])
    #if error:
    #    await ctx.send_followup(error[0], ephemeral=True)
    #    if not error[1]:
    #        return

    error = await trueskill_module.check_valid_name(player_dict["unique_name"])
    if error:
        await ctx.send_followup(error[0], ephemeral=True)
        return

    channel = bot.get_channel(QUEUE_CHANNEL_ID)
    curr_time = datetime.datetime.now(datetime.timezone.utc)
    diff_time = (curr_time - last_ping_queue_nonempty).total_seconds()
    if not players_in_queue and diff_time>PING_QNE_COOLDOWN:
        async for msg in channel.history(limit=2, oldest_first=False):
            if msg.content.startswith("**GET IN HERE"):
                await msg.delete()
        await channel.send(content=f"**GET IN HERE!** 🔥🔥🔥 A player has queued up! RANKED QUEUE OPEN! <@&{CUSTOMS_ROLE_ID}>")
        last_ping_queue_nonempty = curr_time

    player_dict.update({"discord_name":ctx.author.name})
    player_dict.update({"discord_id":ctx.author.id})
    player_dict.update({"min_since":0})

    players_in_queue.append(player_dict)
    await ctx.send_followup(f"Queued up {ctx.author.name}.", ephemeral=True)
    await check_queue()
    
    

@bot.slash_command(name="leave_queue", guild_ids=GUILD_IDS) # Create a slash command
async def leave_queue(ctx):
    """Leave the queue (or remove from game)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global players_in_game
    global players_in_queue

    for player_info in players_in_queue:
        if player_info["discord_id"] == ctx.author.id:
            players_in_queue.remove(player_info)
            await ctx.respond(f"Removed {ctx.author.name} from queue.", ephemeral=True)
            return
    for player_info in players_in_game:
        if player_info["discord_id"] == ctx.author.id:
            players_in_game.remove(player_info)
            await ctx.respond(f"Removed {ctx.author.name} from queue. (They were still in game)", ephemeral=True)
            return
    await ctx.respond(f"{ctx.author.name} not in queue.", ephemeral=True)

@bot.slash_command(name="clear_game", guild_ids=GUILD_IDS) # Create a slash command
async def clear_game(ctx, discord_name: discord.Option(str, required = False, default="")):
    """Clear your current game (or one by name)."""
    global games_in_progress
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    name_chk = ctx.author.name if discord_name == "" else discord_name

    for game in games_in_progress:
        for player in game:
            if player["discord_name"] == name_chk:
                games_in_progress.remove(game)
                await ctx.respond(f"Removed game including {name_chk}. Please queue up again.")
                return
    await ctx.respond(f"{name_chk} is not in a game.")

@bot.slash_command(name="get_games_in_progress", guild_ids=GUILD_IDS) # Create a slash command
async def get_games_in_progress(ctx):
    """Show games currently in progress."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global games_in_progress
    to_print = "**Current matches in progress:** \n"
    for g_info in games_in_progress:
        for p_info in g_info:
            to_print += f"{str(p_info["unique_name"])} - "
        to_print += "**---------------**\n\n"
    await ctx.respond(to_print)

async def get_queue_print():
    """
    Retrieve and format the list of players currently in the queue for printing.
    @return A formatted string listing the current players in the queue.
    """
    global players_in_queue
    to_print = "**Current players in queue:** \n"
    for p_info in players_in_queue:
        to_print += f"{str(p_info["unique_name"])} - "
    return to_print

@bot.slash_command(name="get_queue", guild_ids=GUILD_IDS) # Create a slash command
async def get_queue(ctx):
    """Show current players in queue."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    to_print = await get_queue_print()
    await ctx.respond(to_print)

async def delayed_requeue(players):
    """
    Delay requeue by 30 seconds after a game ends, leaving players time to leave the queue
    """
    await asyncio.sleep(30)

async def game_end(game_index):
    """
    End a game session by removing players from the game in progress and adding them back to the queue. TODO removed auto queue
    @param game_index - the index of the game session to end
    """
    global games_in_progress
    global players_in_game
    global players_in_queue
    for player_info in games_in_progress[game_index]:
        if player_info in players_in_game:
            #players_in_queue.append(player_info)
            players_in_game.remove(player_info)
    games_in_progress.pop(game_index)

@tasks.loop(minutes=1)
async def queue_limit_kicker():
    """
    Every minute, check the queue for players who have been waiting for more than an hour and remove them from the queue. 
    If the queue becomes empty, delete the last message in the queue channel.
    @return None
    """
    global games_in_progress
    global games_in_progress_chk
    global players_in_queue
    #trueskill_module.log_stuff(f"\nPlayers curr in queue: -- {players_in_queue} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    channel = bot.get_channel(MAIN_CHANNEL_ID)

    queuers_to_remove = []
    for i, p_info in enumerate(players_in_queue):
        if p_info["min_since"] >=60:
            trueskill_module.log_stuff(f"\nRemoving {p_info["unique_name"]} from queue for hitting 1 hour  --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
            await channel.send(content=f"<@{p_info["discord_id"]}> removed from queue (hour time limit).")
            queuers_to_remove.append(p_info)
            continue
        p_info["min_since"] += 1
        players_in_queue[i] = p_info
    for p in queuers_to_remove:
        players_in_queue.remove(p)
    if not players_in_queue:
        channel = bot.get_channel(QUEUE_CHANNEL_ID)
        async for msg in channel.history(limit=2, oldest_first=False):
            if msg.content.startswith("**GET IN HERE"):
                await msg.delete()

@tasks.loop(seconds=20)
async def games_queue_logging():
    """
    Asynchronously log the games queue and process games in progress.
    @param None
    @return None
    """
    global games_in_progress
    global games_in_progress_chk
    global players_in_queue
    #trueskill_module.log_stuff(f"\nPlayers curr in queue: -- {players_in_queue} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    channel = bot.get_channel(MAIN_CHANNEL_ID)

    if games_in_progress == []:
        return
    trueskill_module.log_stuff(f"\nGoing through games IN PROGRESS queue -- {games_in_progress} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    
    i = 0
    while i < len(games_in_progress):
        p_lis = games_in_progress[i]
        p_lis_for_chcker = []
        for p_info in p_lis:
            p_lis_for_chcker.append(p_info["unique_name"])
        
        p_info = p_lis[games_in_progress_chk]
            
        trueskill_module.log_stuff(f"\nAttempting log queue entry {p_info["unique_name"]} (in-game)  --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        return_str = await log_recent_game_standalone(p_info["unique_name"], p_lis_for_chcker)
        if not (return_str == None):
            await channel.send(content=return_str)
            await game_end(i)
            i=0
            await check_queue()
            break   
        await asyncio.sleep(1)
        i+=1
    games_in_progress_chk += 1
    if games_in_progress_chk == 8:
        games_in_progress_chk = 0


@tasks.loop(seconds=20)
async def queue_printer():
    """
    Asynchronously check and update the queue status by comparing the current queue length with the previous length. 
    If there is a change in the queue length, update the queue channel and retrieve the latest queue message to display the updated queue status.
    @return None
    """
    global prev_len
    global players_in_queue
    if prev_len != len(players_in_queue):
        await change_q_channel()
        prev_len = len(players_in_queue)
    msg = bot.get_message(QUEUE_MSG_ID)
    await msg.edit(content=await get_queue_print())

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

def testing_helper(author_name):
    """
    A helper function to add a player to the queue for testing purposes.
    @param author_name - the name of the player to be added to the queue.
    """
    global players_in_queue
    player_dict = trueskill_module.get_player_pair_from_discord(author_name)
    
    player_dict.update({"discord_name":author_name})
    player_dict.update({"discord_id":"12345"})
    player_dict.update({"min_since":0})

    players_in_queue.append(player_dict)

@bot.slash_command(name="test_stuff", guild_ids=GUILD_IDS) # Create a slash command
async def test_stuff(ctx):
    """Admin test command for local checks."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id == 118201449392898052: 
        trueskill_module.register("blah", "Tsunani#nani")
        testing_helper("blah")
        trueskill_module.register("blah1", "mvches#mvmv")
        testing_helper("blah1")
        testing_helper("blah2")
        testing_helper("blah3")
        testing_helper("blah4")
        testing_helper("blah5")
        testing_helper("blah6")
        trueskill_module.register("blah2", "Krilo#NUTT")
        trueskill_module.register("blah3", "Despi#derp")
        trueskill_module.register("blah4", "Mitchp#0000")
        trueskill_module.register("blah5", "Stevenator#546")
        trueskill_module.register("blah6", "Matty#9999")
        print(players_in_queue)
        await ctx.respond("Done", ephemeral=True)
        await ctx.edit(content="done edited")
    else:
        await ctx.respond("Not for you", ephemeral=True)

@bot.slash_command(name="reset_players", guild_ids=GUILD_IDS) # Create a slash command
async def reset_players(ctx):
    """Reset player file (admin only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        trueskill_module.reset_player_file()
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)

@bot.slash_command(name="reset_player_stats", guild_ids=GUILD_IDS) # Create a slash command
async def reset_player_stats(ctx):
    """Reset player stats (admin only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        trueskill_module.reset_player_stats()
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)

@bot.slash_command(name="reset_matches", guild_ids=GUILD_IDS) # Create a slash command
async def reset_matches(ctx):
    """Reset match file (admin only)."""
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        trueskill_module.reset_match_file()
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)

async def send_init_q_msg():
    """
    Refresh the queue by deleting old messages and channels, then create new ones to reflect current players.
    @param None
    @return None
    """
    global QUEUE_MSG_ID
    global players_in_queue
    channel = bot.get_channel(QUEUE_CHANNEL_ID)
    async for msg in channel.history(limit=2, oldest_first=False):
        if msg.content.startswith("**Current players") or msg.content.startswith("**GET IN HERE"):
            await msg.delete()
    
    guild = bot.get_guild(GUILD_IDS[0 if TESTING else 1])
    category = bot.get_channel(QUEUE_CAT_ID)
    for vc in guild.voice_channels:
        if vc.name.startswith("🟢"):
            await vc.delete()
    await category.create_voice_channel(name=f"🟢-{len(players_in_queue)}-PLAYERS-IN-QUEUE")
    
    
    msg = await channel.send(content="**Current players in queue:** \n")
    QUEUE_MSG_ID = msg.id

@bot.event
async def on_ready():
    """
    Handle bot startup initialization.
    @param None
    @return None
    """
    print(f'Logged in as {bot.user}', flush=True)
    await send_init_q_msg()
    if not games_queue_logging.is_running():
        games_queue_logging.start()
    if not queue_printer.is_running():
        queue_printer.start()
    if not queue_limit_kicker.is_running():
        queue_limit_kicker.start()
    

load_in_admins()
load_dotenv()
bot.run(os.getenv(BOT_KEY))
