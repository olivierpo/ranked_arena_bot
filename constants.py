import datetime
import sys

GUILD_IDS = [441714985425436701]
MAIN_CHANNEL_ID = 441714985425436703
QUEUE_CHANNEL_ID = 1357474034203230299
CUSTOMS_ROLE_ID=1357831253847576596
QUEUE_CAT_ID = 1357833015539011705


# ##############################  TESTING VARIABLE ################################
TESTING = 1
# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         TESTING = int(sys.argv[1])
# print(TESTING)
# #################################################################################


# if TESTING:
#     BOT_KEY = "TEST_BOT_KEY"
#     GUILD_IDS=[168149897512484866]
#     MAIN_CHANNEL_ID=1352030483076218920
#     QUEUE_CHANNEL_ID=1352030483076218920
#     CUSTOMS_ROLE_ID=1356809301301395537
#     QUEUE_CAT_ID = 1357106979679768748
    
# else:
#     BOT_KEY = "OLIV_BOT_KEY"
#     GUILD_IDS=[168149897512484866, 1313026440660385834]
#     MAIN_CHANNEL_ID=1352484632884416542
#     QUEUE_CHANNEL_ID=1356775280399880272
#     QUEUE_CAT_ID = 1357104967944769666
#     CUSTOMS_ROLE_ID = 1313633911154409564

QUEUE_MSG_ID = 0
MMR_DEFAULT = 1000
CONFIDENCE_DEFAULT = 333
PING_QNE_COOLDOWN = datetime.timedelta(hours=2).total_seconds()

COMMANDS_STRING = """
        **PUBLIC:**
        *<!leaderboard>* Prints leaderboard.
        *<!balance user_name1,username2,...username8>* Prints balanced teams from usernames. No spaces between names, just commas. 
        *</get_player user_name>* Prints player MMR and rank.
        *</add_player user_name>* Adds a player to the ranked system.
        *</log_next_game user_name>* Puts player in logging queue and adds the next viable game in op.gg to the log.
        *</log_recent_game user_name>* Rates most recent game from player IF the game is an arena custom game and ALL PLAYERS are in the system.
        *</log_specific_game match_id>* Rates specific game IF the game is an arena custom game and ALL PLAYERS are in the system.
        *</get_players_list>* Lets you read through all players sorted by rank.

        ***All usernames are CASE SENSITIVE. Please double check!***
        """
