import json

def reset_match_ids():
    match_json = {"match_ids" : ["0246ac68-8b1a-444d-9629-a528e40ec32d"]}

    with open("match_ids.json", "w") as outfile:
        json.dump(match_json, outfile, indent=4)

def reset_player_ids():
    players_json = {"player_ids" : ["3131248f6e5a4c64a1a9664135978d95"], 
                 "player_elos" : {"3131248f6e5a4c64a1a9664135978d95" : [250, 83, "Emperor#King"]}}

    with open("player_ids.json", "w") as outfile:
        json.dump(players_json, outfile, indent=4)
