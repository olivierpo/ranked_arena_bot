from flask import Flask, jsonify, request
import json
from bs4 import BeautifulSoup
import urllib3

app = Flask(__name__)

@app.route('/players', methods=['GET'])
def get_players():
    to_read = ""
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    return jsonify(data=json.dumps(to_read), status=200, mimetype='application/json')

@app.route('/matches', methods=['GET'])
def get_matches():
    to_read = ""
    with open("match_ids.json", "r") as infile:
        to_read = json.load(infile)
    return jsonify(data=json.dumps(to_read), status=200, mimetype='application/json')

@app.route('/add-player', methods=['POST'])
def add_player():
    player_unique_name = request.args.get("player-name")
    #print(player_unique_name)
    username_list = player_unique_name.split("#")
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
    to_append = ""
    with open("player_ids.json", "r") as readfile:
        to_append = json.load(readfile)
    with open("player_ids.json", "w") as writefile:
        to_append["player_ids"].append(user_id)
        to_append["player_elos"].update({user_id:[1000, 100, player_unique_name]})
        json.dump(to_append, writefile, indent=4)
    
    return jsonify({"Response" : "Successfully added player " + str(user_id)})

if __name__ == '__main__':
    app.run()