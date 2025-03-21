import json
import requests
import trueskill
import mpmath
import time
from bs4 import BeautifulSoup
import urllib3

def log_stuff(message):
    with open("match_getter_log.txt", "a") as appendfile:
        appendfile.write(message)

def is_new_game(match_data):
    if match_data["queue_id"] != "customgame":
        return 0
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(to_read["match_ids"])):
            time.sleep(1)
            exit()
            if match_data["match_id"] == to_read["match_ids"][i]:
                return 0
    return 1

def is_players_correct(match_data):
    if len(match_data) > 9:
        print("not arena")
        return 0
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        for i in range(len(match_data)):
            if not (match_data[i]["player_id_encoded"] in to_read["player_ids"]):
                print("not in player ids")
                return 0
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
            if match_data[i]["team_id"] == "0":
                players1.append([match_data[i]["player_id_encoded"], env.create_rating(player_mu, player_sigma), match_data[i]["placement"], match_data[i]["player"]["unique_display_name"]])
            elif match_data[i]["team_id"] == "1":
                players2.append([match_data[i]["player_id_encoded"], env.create_rating(player_mu, player_sigma), match_data[i]["placement"], match_data[i]["player"]["unique_display_name"]])
            else:
                print("MATCH ABORTED. TOO MANY TEAMS")
                return

        #print(players1)
        #print(players2)
        if (len(players1) + len(players2)) > 8:
            print("MATCH ABORTED. MORE THAN 8 PLAYERS")
            return
        rating_groups = [{players1[0][0]: players1[0][1], players1[1][0]: players1[1][1], players1[2][0]: players1[2][1], players1[3][0]: players1[3][1]}, 
                         {players2[0][0]: players2[0][1], players2[1][0]: players2[1][1], players2[2][0]: players2[2][1], players2[3][0]: players2[3][1]}]
        if players1[0][2] == "1":
            ranks = [0, 1]
        else:
            ranks = [1, 0]
        rated_rating_groups = env.rate(rating_groups, ranks)

        #print("\n\n" + str(rated_rating_groups))
        for i in range(4):
            to_read["player_elos"][players1[i][0]][0] = rated_rating_groups[0][players1[i][0]].mu
            to_read["player_elos"][players1[i][0]][1] = rated_rating_groups[0][players1[i][0]].sigma
            to_read["player_elos"][players1[i][0]][2] = players1[i][3]
            
        for i in range(4):
            to_read["player_elos"][players2[i][0]][0] = rated_rating_groups[1][players2[i][0]].mu
            to_read["player_elos"][players2[i][0]][1] = rated_rating_groups[1][players2[i][0]].sigma
            to_read["player_elos"][players2[i][0]][2] = players2[i][3]
    #print("\n\n" + str(to_read))
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
    reply = response.data

    soup = BeautifulSoup(reply, 'html.parser')
    huge_string = soup.find(id="app")
    id_index = str(huge_string).find("user_id")
    #print(id_index)
    display_index = str(huge_string).find("display_name")
    if id_index == -1:
        print("ID not found for displayname")
        return
    user_id = str(huge_string)[id_index+10:display_index-3]
    #lp = soup.find("div", {"class": "lp"}).contents[0]

    #print(huge_string)
    #print(user_id)
    return user_id

def check_new_match(match_id):
    
    ###CHANGE TODO {json_new_match["data"][0]["match_id"]} FOR THE MATCH ID

    match_details = requests.get(f"https://supervive.op.gg/api/matches/steam-{match_id}")
    time.sleep(0.01)
    json_match_details = match_details.json()

    for i in range(len(json_match_details)):
        #print(json_match_details[i])
        json_match_details[i]["player_id_encoded"] = retrieve_id(json_match_details[i]["player"]["unique_display_name"])
    

    if not is_players_correct(json_match_details):
        return

    score_match(json_match_details)
    #TODO change static id
    mark_match_played(match_id)
    #print(json_y)

def check_matches():
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)

        for i in range(len(to_read["player_ids"])):
            #print(f"https://supervive.op.gg/api/players/steam-{to_read["player_ids"][i]}/matches/")
            new_match = requests.get(f"https://supervive.op.gg/api/players/steam-{to_read["player_ids"][i]}/matches/")
            #new_match = requests.get("https://supervive.op.gg/api/players/steam-10570b1ecb3a467083a6ef9b005213f4/matches/")
            time.sleep(0.02)
            #print(new_match)
            json_new_match = new_match.json()

            if not is_new_game(json_new_match["data"][0]):
                continue
        
            check_new_match(json_new_match["data"][0]["match_id"])

def make_backup():
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
        with open("match_ids_backup.json", "a") as appendfile:
            json.dump(to_read, appendfile, indent=4)
    with open("match_ids_backup.json", "a") as appendfile:
            appendfile.write("\n\n"+time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
        with open("player_ids_backup.json", "a") as appendfile:
            json.dump(to_read, appendfile, indent=4)
    with open("player_ids_backup.json", "a") as appendfile:
            appendfile.write("\n\n"+time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))


def start():
    check_new_match("20260306-18a2-4086-a87e-34bbe889d66b")
    while(1):
        counter = 0
        log_stuff(f"\nRunning checkmatches at time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        check_matches()
        time.sleep(300)
        counter = counter + 1
        if counter == 12:
            make_backup()
            counter = 0


start()