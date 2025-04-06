import json

class DatabaseController():
    def __init__(self):
        # init db connection here
        pass

    async def read_match_ids(self):
        with open("match_ids.json", "r") as infile:
            to_read = json.load(infile)
        return to_read

    async def write_match_ids(self, data):
        with open("match_ids.json", "w") as outfile:
            json.dump(data, outfile, indent=4)

    async def read_player_ids(self):
        with open("player_ids.json", "r") as infile:
            to_read = json.load(infile)
        return to_read

    async def write_player_ids(self,data):
        with open("player_ids.json", "w") as outfile:
            json.dump(data, outfile, indent=4)

    async def read_discord_ids(self):
        with open("discord_ids_registered.json", "r") as infile:
            to_read_discord = json.load(infile)
        return to_read_discord

    async def write_discord_ids(self, data):
        with open("discord_ids_registered.json", "w") as outfile:
            json.dump(data, outfile, indent=4)
