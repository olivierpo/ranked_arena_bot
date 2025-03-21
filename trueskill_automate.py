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

reset_module = importlib.import_module("id_reset_module")

sys.stdout.reconfigure(encoding='utf-8')

def log_stuff(message):
    with open("match_getter_log.txt", "a") as appendfile:
        appendfile.write(message)

def is_new_game_from_match_id(match_id):
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(to_read["match_ids"])):
            time.sleep(0.02)
            if match_id == to_read["match_ids"][i]:
                return 0
    return 1

def is_new_game(match_data):
    if match_data["queue_id"] != "customgame":
        return 0
    return is_new_game_from_match_id(match_data["match_id"])



def is_players_correct(match_data):
    changed = 0
    if len(match_data) > 9:
        log_stuff("\nnot arena")
        return 0
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(match_data)):
            if not (match_data[i]["player_id_encoded"] in to_read["player_ids"]):
                log_stuff(f"\n{match_data[i]["player_id_encoded"]}")
                log_stuff(f"\n{match_data[i]["player"]["unique_display_name"]}")
                log_stuff("\nnot in player ids")
                return 0
            if not (match_data[i]["player"]["unique_display_name"] == to_read["player_elos"][match_data[i]["player_id_encoded"]][2]):
                to_read["player_elos"][match_data[i]["player_id_encoded"]][2] = match_data[i]["player"]["unique_display_name"]
                changed = 1
    if changed:
        with open("player_ids.json", "w") as outfile:
            log_stuff("\nplayer username was changed with same id")
            json.dump(to_read, outfile, indent=4)

    return 1

def score_match(match_data):
    to_read = ""
    players1=[]
    players2=[]
    env = trueskill.TrueSkill(backend="mpmath")
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(match_data)):
            player_mu = to_read["player_elos"][match_data[i]["player_id_encoded"]][0]
            player_sigma = to_read["player_elos"][match_data[i]["player_id_encoded"]][1]
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
            to_read["player_elos"][players1[i][0]][0] = rated_rating_groups[0][players1[i][0]].mu
            to_read["player_elos"][players1[i][0]][1] = rated_rating_groups[0][players1[i][0]].sigma
            to_read["player_elos"][players1[i][0]][2] = players1[i][2]
            
        for i in range(4):
            to_read["player_elos"][players2[i][0]][0] = rated_rating_groups[1][players2[i][0]].mu
            to_read["player_elos"][players2[i][0]][1] = rated_rating_groups[1][players2[i][0]].sigma
            to_read["player_elos"][players2[i][0]][2] = players2[i][2]

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
        log_stuff("\nID not found for displayname")
        return
    user_id = str(huge_string)[id_index+10:display_index-3]

    return user_id

"""
Check a match with match id
"""
def check_new_match(match_id):

    if not is_new_game_from_match_id(match_id):  
        log_stuff(f"\n{match_id} Not a valid game")
        return

    match_details = requests.get(f"https://supervive.op.gg/api/matches/steam-{match_id}")
    time.sleep(0.5)

    json_match_details = match_details.json()

    for i in range(len(json_match_details)):
        json_match_details[i]["player_id_encoded"] = retrieve_id(json_match_details[i]["player"]["unique_display_name"])
    

    if not is_players_correct(json_match_details):
        return

    score_match(json_match_details)
    
    mark_match_played(match_id)
    
    print("ended match process")
    return [json_match_details, match_id]

"""
Check a match with player unique name (player's most recent match)
"""
def check_match_w_name(unique_name):
    user_id = retrieve_id(unique_name)

    new_match = requests.get(f"https://supervive.op.gg/api/players/steam-{user_id}/matches?page=1")

    json_new_match = new_match.json()
    if(len(json_new_match["data"]) == 0):
        log_stuff("\nNo match data")
        return
    if not is_new_game(json_new_match["data"][0]):
        
        log_stuff(f"\n{json_new_match["data"][0]["match_id"]} Not a valid game")
        return
   
    log_stuff(f"\ntrueskill-automate checking match: {json_new_match["data"][0]["match_id"]}")
    
    return check_new_match(json_new_match["data"][0]["match_id"])

def check_matches():
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

        check_new_match(json_new_match["data"][0]["match_id"])


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

def reset_match_file():
    make_backup()
    reset_module.reset_match_ids()

def reset_player_file():
    make_backup()
    reset_module.reset_player_ids()

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