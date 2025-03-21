import discord
import logging
import json
from discord.ext import commands
from bs4 import BeautifulSoup
import urllib3
import re
import importlib
import time
import copy
import os
from dotenv import load_dotenv

trueskill_module = importlib.import_module("trueskill_automate")

MMR_DEFAULT = 250
CONFIDENCE_DEFAULT = 83

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents,
                   case_insensitive=False,)

players_in_memory = ""
sorted_players = []
global_admin_list = []

def load_in_admins():
    global global_admin_list
    global_admin_list = [118201449392898052, 242753760890191884]
    with open("admin_list.txt", "r") as readfile:
        for admins in readfile:
            global_admin_list.append(int(admins[:-1]))

def get_players():
    global players_in_memory
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    players_in_memory = to_read
    return to_read

def p1_is_better(player1, player2):
    if player1[0] < player2[0]:
        return 1
    else:
        return 0
    


def get_sorted_players():
    global sorted_players
    global players_in_memory
    players_list = list(players_in_memory["player_elos"].values())
    for i in range(len(players_in_memory["player_ids"])):
        for j in range(len(players_in_memory["player_ids"])):
            if i == j:
                continue
            p1 = players_list[i]
            p2 = players_list[j]
            if p1_is_better(p1, p2):
                continue
            else:
                players_list[i] = p2
                players_list[j] = p1
    #print(players_list)
    sorted_players = players_list

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
        global sorted_players
        leaderboard_str = ""
        for i in range(starting_int, starting_int+10):
            if i >= len(sorted_players):
                break
            leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i][2]} --- "+str(int(sorted_players[i][0])) + "\n")
        new_button_1.label = str(int(new_button_1.label)-10)
        new_button_0.view.children[0] = new_button_1
        new_button_0.view.children[1] = new_button_2
        #print(new_button_0.view.children)
        await interaction.response.edit_message(content=leaderboard_str, view=new_button_0.view)
        #self.refresh()
        #await interaction.response.send_message(, ephemeral=True) # Send a message when the button is clicked

    @discord.ui.button(label="11", style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def second_button_callback(self, button, interaction):
        global sorted_players
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
            leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i][2]} --- "+str(int(sorted_players[i][0])) + "\n")
        new_button_2.label = str(int(new_button_2.label)+10)
        new_button_0.view.children[0] = new_button_1
        new_button_0.view.children[1] = new_button_2
        #print(new_button_0.view.children)
        await interaction.response.edit_message(content=leaderboard_str, view=new_button_0.view)

def fill_next_recur(team1, team2, players_full):
    #print(f"\nteams: {team1} --- {team2} --- {players_full}\n")
    if len(team1) == 4:
        if len(team2) == 4:
            average_team_1 = (team1[0][1] + team1[1][1] + team1[2][1] + team1[3][1])/4.0
            average_team_2 = (team2[0][1] + team2[1][1] + team2[2][1] + team2[3][1])/4.0
            delta = abs(average_team_2 - average_team_1)
            #print("got here\n")
            return [delta, team1, team2]
    #print(f"\nteams: {team1} --- {team2} --- {players_full}\n")
    
    dict_keys = list(players_full.keys())
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
        curr_result = fill_next_recur(temp_team1, temp_team2, temp_players_full)
        if not best_result:
            best_result = curr_result
        else:
            if curr_result[0] < best_result[0]:
                best_result = curr_result
    return best_result

def balance_teams(players_to_balance):
    balance_result = fill_next_recur([], [], players_to_balance)
    return [balance_result[1], balance_result[2]]
    


@bot.event
async def on_message(message):
    global sorted_players
    if message.author == bot.user:
        return
    if message.content.startswith('!hello'):
        trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        await message.reply('Hello!', mention_author=True)
    if message.content.startswith('!leaderboard'):
        trueskill_module.log_stuff(f"\n{message.content} -- {message.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        get_players()
        get_sorted_players()
        leaderboard_str = ""
        #print(sorted_players)
        for i in range(20):
            if i >= len(sorted_players):
                break
            leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i][2]} --- "+str(int(sorted_players[i][0])) + "\n")
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
            if sorted_players[i][2] in balance_player_list:
                dict_to_balance[sorted_players[i][2]] = sorted_players[i][0]
        
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
        command_printable = """
        **PUBLIC:**
        *<!leaderboard>* Prints leaderboard.
        *<!balance user_name1,username2,...username8>* Prints balanced teams from usernames. No spaces between names, just commas. 
        *</get_player user_name>* Prints player MMR and rank.
        *</add_player user_name>* Adds a player to the ranked system.
        *</log_recent_game user_name>* Rates most recent game from player IF the game is an arena custom game and ALL PLAYERS are in the system.
        *</log_specific_game match_id>* Rates specific game IF the game is an arena custom game and ALL PLAYERS are in the system.
        *</get_players_list>* Lets you read through all players sorted by rank.

        ***All usernames are CASE SENSITIVE. Please double check!***
        """
        await message.reply(command_printable, mention_author=True)




@bot.slash_command(name="get_all_players", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def get_all_players(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        player_file = discord.File("./player_ids.json")
        await ctx.send(file=player_file, content="JSON file containing all players.")
    else:
        await ctx.respond("Unauthorized", ephemeral=True)

@bot.slash_command(name="appoint_admin", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def appoint_admin(ctx, admin_to_appoint: discord.Option(str)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id == 118201449392898052:
        with open("admin_list.txt", "a") as readfile:
            readfile.write(admin_to_appoint+"\n")
        load_in_admins()
        await ctx.respond("Admin appointed", ephemeral=True)
    else:
        await ctx.respond("Unauthorized", ephemeral=True)

@bot.slash_command(name="remove_admin", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def remove_admin(ctx, admin_to_remove: discord.Option(str)):
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

@bot.slash_command(name="get_admins", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def get_admins(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global global_admin_list
    if ctx.author.id in global_admin_list:
        await ctx.respond(global_admin_list, ephemeral=True)
    else:
        await ctx.respond("Unauthorized", ephemeral=True)

@bot.slash_command(name="get_all_matches", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def get_all_matches(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        player_file = discord.File("./match_ids.json")
        await ctx.send(file=player_file, content="JSON file containing all matches.")
    else:
        await ctx.respond("Unauthorized", ephemeral=True)

@bot.slash_command(name="get_player", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def get_player(ctx, player_name: discord.Option(str)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global sorted_players
    get_players()
    get_sorted_players()
    for i in range(len(sorted_players)):
        if player_name.lower() == sorted_players[i][2].lower():
            await ctx.respond(f"Name:  **{player_name}**\nMMR:  **{sorted_players[i][0]}**\nRank:  **{i+1}**", ephemeral=True)
            return
        
    await ctx.respond(f"Player {player_name} not found", ephemeral=True)

def get_id_from_name(unique_name):
    username_list = unique_name.split("#")
    #print(username_list)
    remove_whitespace = username_list[0].split()
    num_tokens = len(remove_whitespace)
    if num_tokens > 1:
        token_count = 0
        username_final = remove_whitespace[token_count]
        while num_tokens > 1:
            token_count = token_count + 1
            username_final = username_final + "%20" + remove_whitespace[token_count]
            num_tokens = num_tokens - 1
        username_final = username_final + "%23" + username_list[1]
    else:
        username_final = username_list[0] + "%23" + username_list[1]
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

@bot.slash_command(name="add_player_admin", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def add_player_admin(ctx, player_name: discord.Option(str), player_mmr: discord.Option(float, required = False, default=MMR_DEFAULT), mmr_confidence: discord.Option(float, required = False, default=CONFIDENCE_DEFAULT)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        pattern = re.compile("\\S+.*#\\S+")
        if not pattern.match(player_name):
            await ctx.respond("Inputted name not correct format", ephemeral=True)
            return
        #print(player_unique_name)
        user_id = get_id_from_name(player_name)
        
        if not user_id:
             await ctx.respond(f"Something went wrong", ephemeral=True)
             return
        #lp = soup.find("div", {"class": "lp"}).contents[0]

        #print(huge_string)
        #print(user_id)
        to_append = ""
        with open("player_ids.json", "r") as readfile:
            to_append = json.load(readfile)
        if user_id in to_append["player_ids"]:
            await ctx.respond("Player already in database", ephemeral=True)
            return
        with open("player_ids.json", "w") as writefile:
            to_append["player_ids"].append(user_id)
            to_append["player_elos"].update({user_id:[player_mmr, mmr_confidence, player_name]})
            json.dump(to_append, writefile, indent=4)
        await ctx.respond(f"Added {player_name} successfully", ephemeral=True)
    else:
        await ctx.respond(f"User not authorized", ephemeral=True)

@bot.slash_command(name="add_player", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def add_player(ctx, player_name: discord.Option(str)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    player_mmr = MMR_DEFAULT
    mmr_confidence = CONFIDENCE_DEFAULT
    pattern = re.compile("\\S+.*#\\S+")
    if not pattern.match(player_name):
        await ctx.respond("Inputted name not correct format", ephemeral=True)
        return
    #print(player_unique_name)
    user_id = get_id_from_name(player_name)
    
    if not user_id:
            await ctx.respond(f"Something went wrong", ephemeral=True)
            return
    #lp = soup.find("div", {"class": "lp"}).contents[0]

    #print(huge_string)
    #print(user_id)
    to_append = ""
    with open("player_ids.json", "r") as readfile:
        to_append = json.load(readfile)
    if user_id in to_append["player_ids"]:
        await ctx.respond("Player already in database", ephemeral=True)
        return
    with open("player_ids.json", "w") as writefile:
        to_append["player_ids"].append(user_id)
        to_append["player_elos"].update({user_id:[player_mmr, mmr_confidence, player_name]})
        json.dump(to_append, writefile, indent=4)
    await ctx.respond(f"Added {player_name} successfully", ephemeral=True)

@bot.slash_command(name="update_player", description="attaches json file", guild_ids=[168149897512484866, 1313026440660385834])
async def update_player(ctx, player_name: discord.Option(str), player_mmr: discord.Option(float, required = False, default=MMR_DEFAULT), mmr_confidence: discord.Option(float, required = False, default=CONFIDENCE_DEFAULT)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        pattern = re.compile("\\S+.*#\\S+")
        if not pattern.match(player_name):
            await ctx.respond("Inputted name not correct format", ephemeral=True)
            return
        #print(player_unique_name)
        user_id = get_id_from_name(player_name)
        if not user_id:
             await ctx.respond(f"Something went wrong", ephemeral=True)
             return
        #lp = soup.find("div", {"class": "lp"}).contents[0]

        #print(huge_string)
        #print(user_id)
        to_append = ""
        with open("player_ids.json", "r") as readfile:
            to_append = json.load(readfile)
        with open("player_ids.json", "w") as writefile:
            to_append["player_elos"][user_id]=[player_mmr, mmr_confidence, player_name]
            json.dump(to_append, writefile, indent=4)
        await ctx.respond(f"Updated {player_name} successfully", ephemeral=True)
    else:
        await ctx.respond(f"User not authorized", ephemeral=True)

def get_teams_to_print(match_data):
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


@bot.slash_command(name="log_recent_game", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def log_recent_game(ctx, player_name: discord.Option(str)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    pattern = re.compile("\\S+.*#\\S+")
    if not pattern.match(player_name):
        await ctx.respond("Inputted name not correct format", ephemeral=True)
        return
    await ctx.respond("Loading...")
    match_details_return = trueskill_module.check_match_w_name(player_name)
    match_id_return = match_details_return[1]
    if not match_id_return:
        trueskill_module.log_stuff(f"\n{match_id_return}")
        await ctx.edit(content=f"Could not log match")
        return
    #trueskill_module.log_stuff(f"\n{match_id_return}")
    #trueskill_module.log_stuff(f"\n{match_details_return[0]}")
    printed_content = f"Logged most recent match with id {match_id_return}\n" + get_teams_to_print(match_details_return[0])
    await ctx.edit(content=printed_content)

@bot.slash_command(name="log_specific_game", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def log_specific_game(ctx, match_id: discord.Option(str)):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    await ctx.respond("Loading...")
    match_details_return = trueskill_module.check_new_match(match_id)
    match_id_return = match_details_return[1]
    if not match_id_return:
        trueskill_module.log_stuff(f"\n{match_id_return}")
        await ctx.edit(content=f"Could not log match")
        return
    #43b8e0ae-119c-4631-b18e-346c4b367440
    #print(match_details_return[0])
    printed_content = f"Logged specific match with id {match_id}\n" + get_teams_to_print(match_details_return[0])

    await ctx.edit(content=printed_content)

@bot.slash_command(name="get_players_list", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def get_players_list(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    global sorted_players
    get_players()
    get_sorted_players()
    leaderboard_str = ""
    #print(sorted_players)
    for i in range(10):
        if i >= len(sorted_players):
            break
        leaderboard_str = leaderboard_str+(f"{i+1}. {sorted_players[i][2]} --- "+str(int(sorted_players[i][0])) + "\n")
        

    await ctx.respond(leaderboard_str, view=MyView(), ephemeral=True) # Send a message with our View class that contains the button

@bot.slash_command(name="backup_id_files", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def backup_id_files(ctx):
    if ctx.author.id in global_admin_list:
        trueskill_module.make_backup()
        await ctx.respond("Backed up id files.", ephemeral = True)
    else:
        await ctx.respond("Unauthorized", ephemeral = True)

@bot.slash_command(name="replace_players", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def replace_players(ctx, player_id_json: discord.Attachment):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        await player_id_json.save(fp="./temp_saves/"+player_id_json.filename)
        trueskill_module.replace_pfile_from_file(player_id_json.filename)
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

@bot.slash_command(name="test_stuff", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def test_stuff(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id == 118201449392898052: 
        #await ctx.respond("Done", ephemeral=True)
        #trueskill_module.check_match_w_name("Emperor#King")
        await ctx.respond("Done", ephemeral=True)
        await ctx.edit(content="done edited")
    else:
        await ctx.respond("Not for you", ephemeral=True)

@bot.slash_command(name="reset_players", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def reset_players(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        trueskill_module.reset_player_file()
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)

@bot.slash_command(name="reset_matches", guild_ids=[168149897512484866, 1313026440660385834]) # Create a slash command
async def reset_matches(ctx):
    trueskill_module.log_stuff(f"\n{ctx.command.qualified_name} -- {ctx.author.name} --" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    if ctx.author.id in global_admin_list:
        trueskill_module.reset_match_file()
        await ctx.respond("Done", ephemeral=True)
    else:
        await ctx.respond("Not for you", ephemeral=True)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

load_in_admins()
load_dotenv()
bot.run(os.getenv("OLIV_BOT_KEY"))