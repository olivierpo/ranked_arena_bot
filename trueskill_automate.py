import json
import requests
import trueskill
import mpmath
import time
from bs4 import BeautifulSoup
import urllib3
import codecs
import sys
import os
import importlib
import copy
import asyncio
import builtins

MMR_DEFAULT = 1000
CONFIDENCE_DEFAULT = 333

reset_module = importlib.import_module("id_reset_module")
chrome_module = importlib.import_module("chrome_automation")

sys.stdout.reconfigure(encoding='utf-8')

# Patch open() default
if not getattr(builtins.open, "_is_utf8_patched", False):
    _builtin_open = builtins.open

    def open_utf8_default(*args, **kwargs):
        kwargs.setdefault("encoding", "utf-8")
        return _builtin_open(*args, **kwargs)

    open_utf8_default._is_utf8_patched = True
    builtins.open = open_utf8_default

def log_stuff(message):
    with open("match_getter_log.txt", "a") as appendfile:
        appendfile.write(message)

async def is_new_game_from_match_id(match_id):
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(to_read["match_ids"])):
            await asyncio.sleep(0.02)
            if match_id == to_read["match_ids"][i]:
                return 0
    return 1

async def is_new_game(match_data):
    if match_data["queue_id"] != "customgame":
        return 0
    return await is_new_game_from_match_id(match_data["match_id"])



def is_players_correct(match_data):
    changed = 0
    if len(match_data) > 9:
        log_stuff("\nnot arena")
        return 0
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(match_data)):
            if not (match_data[i]["player_id_encoded"] in to_read.keys()):
                log_stuff(f"\n{match_data[i]["player_id_encoded"]}")
                log_stuff(f"\n{match_data[i]["player"]["unique_display_name"]}")
                log_stuff("\nnot in player ids")
                return 0
            if not (match_data[i]["player"]["unique_display_name"] == to_read[match_data[i]["player_id_encoded"]]["unique_name"]):
                to_read[match_data[i]["player_id_encoded"]]["unique_name"] = match_data[i]["player"]["unique_display_name"]
                changed = 1
    if changed:
        with open("player_ids.json", "w") as outfile:
            log_stuff("\nplayer username was changed with same id")
            json.dump(to_read, outfile, indent=4)

    return 1

def get_squished_mmr(curr_mmr, new_mmr, did_win):
    mmr_delta = abs(new_mmr - curr_mmr)
    if mmr_delta == 0:
        mmr_delta = 1
        if did_win:
            new_mmr = curr_mmr + 1
        else:
            new_mmr = curr_mmr - 1
    if mmr_delta < 20:
        mmr_delta = 20
    elif mmr_delta > 40:
        mmr_delta = 40
    if new_mmr < curr_mmr:
        mmr_delta *= -1
     
    return (curr_mmr + mmr_delta)

def get_pretty_print_from_mmr(mmr):
    ranked_dict = {"Bronze":(0, 499), "Silver":(500, 999), "Gold":(1000, 1499), "Platinum":(1500, 1999), "Diamond":(2000, 2499), "Masters":(2500, 2999), "Challenger":(3000, 100000)}

    for key, value in ranked_dict.items():
        if mmr >= value[0] and mmr <= value[1]:
            if key != "Challenger":
                mmr -= value[0]
                mmr += 100
                division = 6 - int(str(mmr)[:1])
                div_lp = str(mmr)[1:3]
                return (f"{key} {division}   {div_lp} LP")
            else:
                mmr -= value[0]
                return (f"{key}   {mmr} LP") 
    
    print("failure in pretty printing mmr")

def populate_data_players(match_data):
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(match_data)):
            to_read[match_data[i]["player_id_encoded"]]["stats"]["kills"] += match_data[i]["stats"]["Kills"]
            to_read[match_data[i]["player_id_encoded"]]["stats"]["deaths"] += match_data[i]["stats"]["Deaths"]
            to_read[match_data[i]["player_id_encoded"]]["stats"]["assists"] += match_data[i]["stats"]["Assists"]
            to_read[match_data[i]["player_id_encoded"]]["stats"]["damage_done"] += match_data[i]["stats"]["HeroEffectiveDamageDone"]
            to_read[match_data[i]["player_id_encoded"]]["stats"]["damage_taken"] += match_data[i]["stats"]["HeroEffectiveDamageTaken"]
            to_read[match_data[i]["player_id_encoded"]]["stats"]["healing_done"] += match_data[i]["stats"]["HealingGiven"]
            to_read[match_data[i]["player_id_encoded"]]["stats"]["healing_done"] += match_data[i]["stats"]["HealingGivenSelf"]
    with open("player_ids.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4)

def update_new_name_d_ids(player_id, unique_name):
    to_read = ""
    with open("discord_ids_registered.json", "r") as infile:
        to_read = json.load(infile)
        for key, value in to_read.items():
            if value["ingame_id"] == player_id and value["unique_name"] != unique_name:
                log_stuff(f"{value['unique_name']} NAME CHANGED to {unique_name}")
                value["unique_name"] = unique_name
                to_read[key] = value
                break
    with open("discord_ids_registered.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4) 

def update_new_name_p_ids(player_id, unique_name):
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)

        if to_read[player_id]["unique_name"] != unique_name:
            log_stuff(f"{to_read[player_id]['unique_name']} NAME CHANGED to {unique_name}")
            to_read[player_id]["unique_name"] = unique_name
                
    with open("player_ids.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4) 

def score_match(match_data):
    to_read = ""
    players1=[]
    players2=[]
    env = trueskill.TrueSkill(backend="mpmath")
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(match_data)):
            player_mu = to_read[match_data[i]["player_id_encoded"]]["mmr"]
            player_sigma = to_read[match_data[i]["player_id_encoded"]]["sigma"]
            if match_data[i]["placement"] == 1:
                players1.append([match_data[i]["player_id_encoded"], env.create_rating(player_mu, player_sigma), match_data[i]["player"]["unique_display_name"]])
            elif match_data[i]["placement"] == 2:
                players2.append([match_data[i]["player_id_encoded"], env.create_rating(player_mu, player_sigma), match_data[i]["player"]["unique_display_name"]])
            else:
                log_stuff(f"\n{match_data[i]["placement"]}")
                log_stuff("\nMATCH ABORTED. TOO MANY TEAMS")
                return


        if (len(players1) + len(players2)) > 8:
            log_stuff("\nMATCH ABORTED. MORE THAN 8 PLAYERS")
            return
        rating_groups = [{players1[0][0]: players1[0][1], players1[1][0]: players1[1][1], players1[2][0]: players1[2][1], players1[3][0]: players1[3][1]}, 
                         {players2[0][0]: players2[0][1], players2[1][0]: players2[1][1], players2[2][0]: players2[2][1], players2[3][0]: players2[3][1]}]
        ranks = [0, 1]
        rated_rating_groups = env.rate(rating_groups, ranks)


        for i in range(4):
            elo_to_give = get_squished_mmr(to_read[players1[i][0]]["mmr"], rated_rating_groups[0][players1[i][0]].mu, 1)
            to_read[players1[i][0]]["mmr"] = elo_to_give
            to_read[players1[i][0]]["sigma"] = rated_rating_groups[0][players1[i][0]].sigma
            to_read[players1[i][0]]["unique_name"] = players1[i][2]
            to_read[players1[i][0]]["wins"] += 1
            update_new_name_d_ids(players1[i][0], players1[i][2])
            
        for i in range(4):
            elo_to_give = get_squished_mmr(to_read[players2[i][0]]["mmr"], rated_rating_groups[1][players2[i][0]].mu, 0)
            to_read[players2[i][0]]["mmr"] = elo_to_give
            to_read[players2[i][0]]["sigma"] = rated_rating_groups[1][players2[i][0]].sigma
            to_read[players2[i][0]]["unique_name"] = players2[i][2]
            to_read[players2[i][0]]["losses"] += 1
            update_new_name_d_ids(players2[i][0], players2[i][2])

    with open("player_ids.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4)
    
def mark_match_played(match_id):
    to_read = ""
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
        to_read["match_ids"].append(match_id)
    with open("match_ids.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4)

def retrieve_id(username):
    username_list = username.split("#")

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
    
    reply = response.data

    soup = BeautifulSoup(reply, 'html.parser')
    huge_string = soup.find(id="app")
    id_index = str(huge_string).find("user_id")

    display_index = str(huge_string).find("display_name")
    if id_index == -1:
        log_stuff(f"\nID not found for {username}")
        return
    user_id = str(huge_string)[id_index+10:display_index-3]

    return user_id

def is_valid_match(match_data):
    total_kills = 0
    for player_data in match_data:
        total_kills += player_data["stats"]["Kills"]
    if total_kills < 5:
        return 0
    else:
        return 1

def match_all_players(match_det, player_lis):
    for player_info in match_det:
        
        if player_info["player"]["unique_display_name"] not in player_lis:
            return False
    return True

def get_urlsafe_name(unique_name):
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
    return username_final

from concurrent.futures.thread import ThreadPoolExecutor
executor = ThreadPoolExecutor(10)
fetch_lock = asyncio.Lock()
HC = chrome_module.HeadlessChrome()
async def fetch_opgg_match(player_name):
    global HC
    async with fetch_lock:
        try:
            HC.driver.current_url
        except:
            HC = chrome_module.HeadlessChrome()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, HC.fetch_new_matches, get_urlsafe_name(player_name))
        if result:
            log_stuff(f"\nFetched new matches for -- {player_name} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
            await asyncio.sleep(3)
            return 1
        else:
            log_stuff(f"\nFAILED to fetch matches for -- {player_name} -- " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
            await asyncio.sleep(3)
            return 0
    

match_getter_lock = asyncio.Lock()
"""
Check a match with match id
"""
async def check_new_match(match_id, players_list=[]):
    loop = asyncio.get_event_loop()
    async with match_getter_lock:
        if not await is_new_game_from_match_id(match_id):  
            log_stuff(f"\n{match_id} Not a valid game")
            return [f"{match_id} has already been logged. Perhaps try again later?"]
        try:
            match_details = await loop.run_in_executor(executor, requests.get, f"https://supervive.op.gg/api/matches/steam-{match_id}")
        except Exception as error:
            log_stuff(f"Error in request https://supervive.op.gg/api/matches/steam-{match_id}\n" + str(error))
            return ["Error in http request."]
        await asyncio.sleep(0.5)

        json_match_details = match_details.json()

        if players_list:
            res = match_all_players(json_match_details, players_list)
            if not res:
                log_stuff(f"\n{match_id} Didn't have all players in {players_list}.")
                return [f"\n{match_id} Didn't have all players in {players_list}."]

        if not is_valid_match(json_match_details):
            return ["Invalid match (probably too few kills)"]

        for i in range(len(json_match_details)):
            retrieved_id = retrieve_id(json_match_details[i]["player"]["unique_display_name"])
            if not retrieved_id:
                return ["A player was not found in op.gg database"]
            json_match_details[i]["player_id_encoded"] = retrieved_id
        

        if not is_players_correct(json_match_details):
            return ["A player was not found in ranked system"]

        mark_match_played(match_id)
    score_match(json_match_details)
    populate_data_players(json_match_details)
    
    
    #print("ended match process")
    return [json_match_details, match_id]



"""
Check a match with player unique name (player's most recent match)
"""
async def check_match_w_name(unique_name, players_list=[]):
    loop = asyncio.get_event_loop()
    error = await fetch_opgg_match(unique_name)
    if not error:
        log_stuff(f"\nFailed to fetch new matches for {unique_name}")
        return [f"\nFailed to fetch new matches for {unique_name}"]
    user_id = retrieve_id(unique_name)

    try:
        new_match = await loop.run_in_executor(executor, requests.get, f"https://supervive.op.gg/api/players/steam-{user_id}/matches?page=1")
    except Exception as error:
        log_stuff(f"\nError in request https://supervive.op.gg/api/players/steam-{user_id}/matches?page=1"+str(error))
        return ["Error in http request."]

    json_new_match = new_match.json()
    if(len(json_new_match["data"]) == 0):
        log_stuff("\nNo match data")
        return [f"No match data for {unique_name}"]
    if not await is_new_game(json_new_match["data"][0]):
        
        log_stuff(f"\n{json_new_match["data"][0]["match_id"]} Not a valid game")
        return [f"\n{json_new_match["data"][0]["match_id"]} already exists or is not a custom game. Try again later maybe?"]
   
    log_stuff(f"\ntrueskill-automate checking match: {json_new_match["data"][0]["match_id"]}")
    
    return await check_new_match(json_new_match["data"][0]["match_id"], players_list)

def fix_name_manual(new_name, user_ID):
    update_new_name_d_ids(user_ID, new_name)
    update_new_name_p_ids(user_ID, new_name)

"""
Get unique name from ID and fix databases (player_ids and discord_ids_registered) 
"""
async def fix_name_from_ID(user_ID):
    loop = asyncio.get_event_loop()
    try:
        new_match = await loop.run_in_executor(executor, requests.get, f"https://supervive.op.gg/api/players/steam-{user_ID}/matches?page=1")
    except Exception as error:
        log_stuff(f"\nError in request https://supervive.op.gg/api/players/steam-{user_ID}/matches?page=1"+str(error))
        return ["Error in http request to get matches.", 0]
    json_new_match = new_match.json()
    player_id_encoded = json_new_match["data"][0]["player_id_encoded"]
    match_id = json_new_match["data"][0]["match_id"]
    try:
        new_match = await loop.run_in_executor(executor, requests.get, f"https://supervive.op.gg/api/matches/steam-{match_id}")
    except Exception as error:
        log_stuff(f"\nError in request https://supervive.op.gg/api/matches/steam-{match_id}"+str(error))
        return ["Error in http request to get last match data.", 0]
    
    json_new_match = new_match.json()
    player_display_name = ""
    for player in json_new_match:
        if player["player_id_encoded"] == player_id_encoded:
            player_display_name = player["player"]["unique_display_name"]

    if not retrieve_id(player_display_name):
        log_stuff(f"Last match name, {player_display_name}, too old.")
        return [f"Last match name, {player_display_name}, too old.", 1]

    update_new_name_d_ids(user_ID, player_display_name)
    update_new_name_p_ids(user_ID, player_display_name)
    return None

"""
Check a match with player unique ID (player's most recent match)

async def check_match_w_ID(unique_name, players_list=[]):
    loop = asyncio.get_event_loop()
    error = await fetch_opgg_match(unique_name)
    if not error:
        log_stuff(f"\nFailed to fetch new matches for {unique_name}")
        return [f"\nFailed to fetch new matches for {unique_name}"]
    user_id = retrieve_id(unique_name)

    try:
        new_match = await loop.run_in_executor(executor, requests.get, f"https://supervive.op.gg/api/players/steam-{user_id}/matches?page=1")
    except Exception as error:
        log_stuff(f"\nError in request https://supervive.op.gg/api/players/steam-{user_id}/matches?page=1"+str(error))
        return ["Error in http request."]

    json_new_match = new_match.json()
    if(len(json_new_match["data"]) == 0):
        log_stuff("\nNo match data")
        return [f"No match data for {unique_name}"]
    if not await is_new_game(json_new_match["data"][0]):
        
        log_stuff(f"\n{json_new_match["data"][0]["match_id"]} Not a valid game")
        return [f"\n{json_new_match["data"][0]["match_id"]} already exists or is not a custom game. Try again later maybe?"]
   
    log_stuff(f"\ntrueskill-automate checking match: {json_new_match["data"][0]["match_id"]}")
    
    return await check_new_match(json_new_match["data"][0]["match_id"], players_list)"""


"""def check_matches():
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    for i in range(len(to_read["player_ids"])):

        new_match = requests.get(f"https://supervive.op.gg/api/players/steam-{to_read["player_ids"][i]}/matches/")
        #new_match = requests.get("https://supervive.op.gg/api/players/steam-12d41024686a469bb4585a9a56f1b863/matches?amount=1")
        time.sleep(0.5)

        json_new_match = new_match.json()

        if(len(json_new_match["data"]) == 0):
            continue

        if not is_new_game(json_new_match["data"][0]):
            continue

        check_new_match(json_new_match["data"][0]["match_id"])"""

def remove_player_w_id(user_id):
    to_replace = ""
    with open("player_ids.json", "r") as readfile:
        to_replace = json.load(readfile)
    if not user_id in to_replace.keys():
        log_stuff("Player not in database")
        return "Player not in database"
    with open("player_ids.json", "w") as writefile:
        del to_replace[user_id]
        json.dump(to_replace, writefile, indent=4)

def remove_player_w_name(user_name):
    return remove_player_w_id(retrieve_id(user_name))

def add_player(user_id, user_name, mmr=MMR_DEFAULT, sigma=CONFIDENCE_DEFAULT):
    to_append = ""
    with open("player_ids.json", "r") as readfile:
        to_append = json.load(readfile)
    if user_id in to_append.keys():
        log_stuff("Player already in database")
        return "Player already in database"
    with open("player_ids.json", "w") as writefile:
        to_append.update({user_id:{"mmr":mmr, "sigma":sigma, "unique_name": user_name, "wins":0, "losses":0, 
                           "stats":{"kills":0, "deaths":0, "assists":0, "damage_done":0, "damage_taken": 0, "healing_done":0}}})
        json.dump(to_append, writefile, indent=4)

def add_player_w_name(user_name, mmr=MMR_DEFAULT, sigma=CONFIDENCE_DEFAULT):
    return add_player(retrieve_id(user_name), user_name, mmr=mmr, sigma=sigma)

def update_player(user_id, user_name, mmr=MMR_DEFAULT, sigma=CONFIDENCE_DEFAULT):
    to_append = ""
    with open("player_ids.json", "r") as readfile:
        to_append = json.load(readfile)
    if not user_id in to_append.keys():
        log_stuff("Player not in database")
        return "Player not in database"
    with open("player_ids.json", "w") as writefile:
        to_append[user_id]["mmr"]= mmr if mmr != -1 else to_append[user_id]["mmr"]
        to_append[user_id]["sigma"]= sigma if sigma != -1 else to_append[user_id]["sigma"]
        to_append[user_id]["unique_name"]= user_name
        json.dump(to_append, writefile, indent=4)

def update_player_w_name(user_name, mmr=MMR_DEFAULT, sigma=CONFIDENCE_DEFAULT):
    return update_player(retrieve_id(user_name), user_name, mmr=mmr, sigma=sigma)

def make_backup():
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
        with open("./json_backups/match_ids_backup.json", "a") as appendfile:
            json.dump(to_read, appendfile, indent=4)
    with open("./json_backups/match_ids_backup.json", "a") as appendfile:
            appendfile.write("\n\n"+time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        with open("./json_backups/player_ids_backup.json", "a") as appendfile:
            json.dump(to_read, appendfile, indent=4)
    with open("./json_backups/player_ids_backup.json", "a") as appendfile:
            appendfile.write("\n\n"+time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

def replace_pfile_from_file(temp_file_name):
    make_backup()
    with open("./temp_saves/"+temp_file_name, "r") as infile:
        temp_data = json.load(infile)
        with open("player_ids.json", "w") as outfile:
            json.dump(temp_data, outfile, indent=4)

    #TODO maybe eventually remove temp files?
    #os.remove("./temp_saves/"+temp_file_name)

def get_id_from_name_local(ig_name):
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for key, value in to_read.items():
            if value["unique_name"] == ig_name:
                return key
        
async def fill_next_recur(team1, team2, players_full):
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
            temp_team2.append([dict_keys[i], players_full[dict_keys[i]]["mmr"]])
        else:
            temp_team1.append([dict_keys[i], players_full[dict_keys[i]]["mmr"]])
        temp_players_full = copy.deepcopy(players_full)
        temp_players_full.pop(dict_keys[i])
        curr_result = await fill_next_recur(temp_team1, temp_team2, temp_players_full)
        if not best_result:
            best_result = curr_result
        else:
            if curr_result[0] < best_result[0]:
                best_result = curr_result
    return best_result

def get_player_from_discord_balance(discord_id):
    to_read_discord = ""
    to_read = ""
    with open("discord_ids_registered.json", "r") as infile:
        to_read_discord = json.load(infile)
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    
    try:
        return {to_read_discord[discord_id]["unique_name"]:to_read[to_read_discord[discord_id]["ingame_id"]]}
    except:
        log_stuff(f"{discord_id} not in registered users")
        return f"{discord_id} not in registered users"

"""def get_player_from_discord(discord_id):
    to_read_discord = ""
    to_read = ""
    with open("discord_ids_registered.json", "r") as infile:
        to_read_discord = json.load(infile)
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    
    try:
        return {to_read_discord[discord_id]["unique_name"]:to_read_discord[discord_id]["unique_name"]}
    except:
        log_stuff(f"{discord_id} not in registered users")
        return f"{discord_id} not in registered users"""
    
def get_player_pair_from_discord(discord_id):
    to_read_discord = ""

    with open("discord_ids_registered.json", "r") as infile:
        to_read_discord = json.load(infile)
    
    try:
        return {"ingame_id":to_read_discord[discord_id]["ingame_id"],"unique_name":to_read_discord[discord_id]["unique_name"]}
    except:
        log_stuff(f"{discord_id} not in registered users")
        return f"{discord_id} not in registered users"
    

async def balance_teams(discord_ids_to_balance):
    players_to_balance = {}
    for discord_id in discord_ids_to_balance:
        players_to_balance.update(get_player_from_discord_balance(discord_id))
    balance_result = await fill_next_recur([], [], players_to_balance)
    return [balance_result[1], balance_result[2]]

def register(discord_id, ig_name):
    to_read = ""
    with open("discord_ids_registered.json", "r") as infile:
        to_read = json.load(infile)
    if discord_id in to_read.keys():
        log_stuff(f"You've already registered. {discord_id}  {ig_name}")
        return "You've already registered."  
    ingame_id = get_id_from_name_local(ig_name)
    if not ingame_id:
        log_stuff(f"Name not found in local database.  {discord_id}  {ig_name}")
        return "Name not found in local database."  
    to_read.update({discord_id: {"ingame_id":ingame_id, "unique_name":ig_name}})
    with open("discord_ids_registered.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4)

def reset_match_file():
    make_backup()
    reset_module.reset_match_ids()

def reset_player_file():
    make_backup()
    reset_module.reset_player_ids()

def reset_player_stats():
    make_backup()
    reset_module.reset_player_stats()

def start():
    #check_new_match("20260306-18a2-4086-a87e-34bbe889d66b")
    #while(1):
    counter = 0
    log_stuff(f"\nRunning checkmatches at time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    #check_matches()
    #time.sleep(300)
    check_match_w_name("Emperor#King")
    counter = counter + 1
    if counter == 12:
        make_backup()
        counter = 0

#check_match_w_name("Emperor#King")
#print(check_new_match("43b8e0ae-119c-4631-b18e-346c4b367440"))