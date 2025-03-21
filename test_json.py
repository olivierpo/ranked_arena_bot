import json
import trueskill
import mpmath
import time

match_jason = {"match_ids" : ["0246ac68-8b1a-444d-9629-a528e40ec32d", "7df8927b-65de-496e-a158-09f4386c27ae"]}

with open("match_ids.json", "w") as outfile:
    json.dump(match_jason, outfile, indent=4)

with open("match_ids.json", "r") as infile:
    to_read = json.load(infile)
    print(to_read)

"""
10570b1ecb3a467083a6ef9b005213f4
44c34e9bc8c44d4db7f08c42ae2f5146
59475f9ba57a4dc383f05a711509b246
6156268a6ba2457a981b64804abffb5d
8ecc314f8dc54ac5bd14bf9d84dad1de
946c94c0f9bc4b60b556bf1882ad4804
bcffba6721c74bf7a1d494e15e2d655c
c66bb424e1e64798b3f7aa0b4868deb4

"""

players_jason = {"player_ids" : ["10570b1ecb3a467083a6ef9b005213f4", "44c34e9bc8c44d4db7f08c42ae2f5146", "59475f9ba57a4dc383f05a711509b246", "6156268a6ba2457a981b64804abffb5d", "8ecc314f8dc54ac5bd14bf9d84dad1de",
                                 "946c94c0f9bc4b60b556bf1882ad4804", "bcffba6721c74bf7a1d494e15e2d655c", "c66bb424e1e64798b3f7aa0b4868deb4"], 
                 "player_elos" : {"10570b1ecb3a467083a6ef9b005213f4" : [1000, 100, "random garbage"]}}

with open("player_ids.json", "w") as outfile:
    for i in range(len(players_jason["player_ids"])):
        players_jason["player_elos"].update({players_jason["player_ids"][i] : [1000, 100, "random garbage"]})
    json.dump(players_jason, outfile, indent=4)
with open("player_ids.json", "r") as infile:
    to_read = json.load(infile)
    print(to_read)
"""
to_overwrite = ""
with open("player_ids.json", "r") as infile:
    to_read = json.load(infile)
    print(to_read)
    env = trueskill.TrueSkill(backend='mpmath')
    p1_rating = env.create_rating(to_read["player_elos"][to_read["player_ids"][0]][0], to_read["player_elos"][to_read["player_ids"][0]][1])
    print(str(to_read["player_elos"][to_read["player_ids"][0]][0]))
    print(p1_rating)
    p2_rating = env.create_rating(to_read["player_elos"][to_read["player_ids"][0]][0], to_read["player_elos"][to_read["player_ids"][0]][1])
    print(p2_rating)
    p1 = ["3131248f6e5a4c64a1a9664135978d95", 0, p1_rating]
    p2 = ["50e7725ba7734056a55e02637886962d", 1, p2_rating]

    rating_groups = [{"3131248f6e5a4c64a1a9664135978d95": p1[2]}, {"50e7725ba7734056a55e02637886962d": p2[2]}]

    rated_rating_groups = env.rate(rating_groups, ranks=[0, 1])

    p1[2] = rated_rating_groups[0]["3131248f6e5a4c64a1a9664135978d95"]
    p2[2] = rated_rating_groups[1]["50e7725ba7734056a55e02637886962d"]
    print(p1[2])
    print(p2[2])

    to_read["player_elos"]["3131248f6e5a4c64a1a9664135978d95"] = [p1[2].mu, p1[2].sigma]
    to_read["player_elos"]["50e7725ba7734056a55e02637886962d"] = [p2[2].mu, p2[2].sigma]
    to_overwrite = to_read
    #rating_groups = []

with open("player_ids.json", "w") as outfile:
    json.dump(to_overwrite, outfile, indent=4)


"""

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