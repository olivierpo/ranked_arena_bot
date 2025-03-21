from bs4 import BeautifulSoup
import urllib3

"""
        Parameters
        ----------
        server : str
            The server abreviation as used in the op gg url -> "euw", "na", "kr" etc.
        username : str
            The username and the Riot tag seperated by a "-" -> "your_name-Riot_tag"
"""
def retrieve_rank(server, username):
    username_list = username.split("#")
    print(username_list)
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
    print(id_index)
    display_index = str(huge_string).find("display_name")
    if id_index == -1:
        print("notfound")
        return
    user_id = str(huge_string)[id_index+10:display_index-3]
    #lp = soup.find("div", {"class": "lp"}).contents[0]

    #print(huge_string)
    print(user_id)

retrieve_rank("", "Despi#derp")


"""
61ac32c7

"""