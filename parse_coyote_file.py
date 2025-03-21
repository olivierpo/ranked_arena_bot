import requests
import json
from bs4 import BeautifulSoup
import urllib3
import copy
import time
import sys

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

def remove_hash_wh(unique_name):
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

def find_real_case(name_t_s):
    name_t_s_fixed = remove_hash_wh(name_t_s)
    print(f"https://supervive.op.gg/api/players/search?query={name_t_s_fixed}")
    z = requests.get(f"https://supervive.op.gg/api/players/search?query={name_t_s_fixed}")
    
    #print(z.content)
    json_z = z.json()
    for i in range(len(json_z)):
        if json_z[i]["uniqueDisplayName"].lower() == name_t_s.lower():
            sys.stdout.flush()
            time.sleep(3)
            #print("done")
            return json_z[i]["uniqueDisplayName"]
    time.sleep(3)
    print("failed again")

with open("./test_files/mmrs.txt", "r") as infile:
    count = 0
    real_name = ""
    mmr = 0
    confidence = 0
    names_manual = []
    name_to_search = ""
    for line in infile:
        if count == 0:
            mmr = float(line[:-2])
        if count == 1:
            confidence = float(line[:-2])
        if count == 2:
            name_to_search = line[1:-2]
            #print(name_to_search)
            real_name = find_real_case(name_to_search)
            #print()
        if count == 3:
            print([mmr, confidence, real_name])
            if not real_name:
                names_manual.append([mmr, confidence, name_to_search])
                count = 0
                continue
            user_id = get_id_from_name(real_name)
        
            if not user_id:
                print("no dice on userid")
                count = 0
                continue
            #lp = soup.find("div", {"class": "lp"}).contents[0]

            #print(huge_string)
            #print(user_id)
            to_append = ""
            with open("player_ids.json", "r") as readfile:
                to_append = json.load(readfile)
            if user_id in to_append["player_ids"]:
                print("Player already in database")
                count = 0
                continue
            with open("player_ids.json", "w") as writefile:
                to_append["player_ids"].append(user_id)
                to_append["player_elos"].update({user_id:[mmr*10, confidence*10, real_name]})
                json.dump(to_append, writefile, indent=4)
            count = -1
        count+=1
    print(names_manual)



z = requests.get(f"https://supervive.op.gg/api/players/search?query=geb%231087")
print(z.content)