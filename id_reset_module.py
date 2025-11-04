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



def reset_player_stats():
    to_read={}
    with open("player_ids.json", "r") as infile:
        to_read = json.load(infile)
    
    for player_id in to_read:
        to_read[player_id]["mmr"] = 1000
        to_read[player_id]["sigma"] = 333
        to_read[player_id]["wins"] = 0
        to_read[player_id]["losses"] = 0
        to_read[player_id]["stats"]["kills"] = 0
        to_read[player_id]["stats"]["deaths"] = 0
        to_read[player_id]["stats"]["assists"] = 0
        to_read[player_id]["stats"]["damage_done"] = 0
        to_read[player_id]["stats"]["damage_taken"] = 0
        to_read[player_id]["stats"]["healing_done"] = 0
    with open("player_ids.json", "w") as outfile:
        json.dump(to_read, outfile, indent=4)


