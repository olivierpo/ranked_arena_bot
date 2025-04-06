from db.db_controller import DatabaseController as db

async def _get_players():
    '''
    returns all players
    '''
    to_read = await db.read_player_ids()
    return to_read
    
def _p1_is_worse(player1, player2):
    if player1["mmr"] < player2["mmr"]:
        return 1
    else:
        return 0

async def get_sorted_players():
    '''
    ranks players by elo using bubble sort

    creates new global variable `sorted_players`

    `[[250, 100, "Player1Name#ID"], [200, 100, "Player2Name#ID"]]`
    '''
    players_in_memory = await _get_players()
    players_list = list(players_in_memory.values())
    for i in range(len(players_in_memory.keys())):
        for j in range(len(players_in_memory.keys())):
            if i == j:
                continue
            p1 = players_list[i]
            p2 = players_list[j]
            if _p1_is_worse(p1, p2):
                continue
            else:
                players_list[i] = p2
                players_list[j] = p1
    #print(players_list)
    sorted_players = players_list
    return sorted_players
    
