import requests
import json
from bs4 import BeautifulSoup
import urllib3
import copy
import time
import sys
import os
from dotenv import load_dotenv
#x = requests.get("https://supervive.op.gg/api/matches/steam-e73192d5-1560-4a85-b813-afd96d07f301?teamId=0")
#print(x.text)

#y = requests.get("https://player-stats-jx-prod.prodcluster.awsinfra.theorycraftgames.com/player-stats/players/3131248f6e5a4c64a1a9664135978d95")
#print(y)

#z = requests.post("https://accounts.projectloki.theorycraftgames.com/iam/v3/login")
#print(z)

#Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImE5Njg5ZGYxNzVhZWU2OTI1MWY4MDZlNzc4Zjg5MzYwZjNmMjQ0YTMiLCJ0eXAiOiJKV1QifQ.eyJiYW5zIjpbXSwiY2xpZW50X2lkIjoiYmE4ZmI1OWEzNGJiNDgxYWJjYTA4YzQ2YmE0ODgwMjUiLCJjb3VudHJ5IjoiQ0EiLCJkaXNwbGF5X25hbWUiOiJFbXBlcm9yIiwiZXhwIjoxNzQyMjY3NDM5LCJpYXQiOjE3NDIyNjM4MzksImlwZiI6InN0ZWFtIiwiaXNfY29tcGx5Ijp0cnVlLCJpc3MiOiJodHRwczovL2FjY291bnRzLnByb2plY3Rsb2tpLnRoZW9yeWNyYWZ0Z2FtZXMuY29tIiwiamZsZ3MiOjEsIm5hbWVzcGFjZSI6Imxva2kiLCJuYW1lc3BhY2Vfcm9sZXMiOlt7Im5hbWVzcGFjZSI6Imxva2kiLCJyb2xlSWQiOiJjNGMwMmQxYTZlNzg0Mzc5YjY4ZjhkNDMwN2UxYWNlOSJ9LHsibmFtZXNwYWNlIjoibG9raSIsInJvbGVJZCI6Ijg1MGZlOWE1MDBiNzQzYTQ5OGUyMTlmOTRkNjMzYTE5In0seyJuYW1lc3BhY2UiOiJ0aGVvcnljcmFmdCIsInJvbGVJZCI6IjIyNTE0Mzg4MzllOTQ4ZDc4M2VjMGU1MjgxZGFmMDViIn0seyJuYW1lc3BhY2UiOiJsb2tpIiwicm9sZUlkIjoiMjI1MTQzODgzOWU5NDhkNzgzZWMwZTUyODFkYWYwNWIifV0sInBlcm1pc3Npb25zIjpbXSwicm9sZXMiOltdLCJzY29wZSI6ImFjY291bnQgY29tbWVyY2Ugc29jaWFsIHB1Ymxpc2hpbmcgYW5hbHl0aWNzIiwic3ViIjoiMzEzMTI0OGY2ZTVhNGM2NGExYTk2NjQxMzU5NzhkOTUiLCJ1bmlvbl9pZCI6IjMxNmM3MjJhOTU2NjQ4MWJhYTlmYzQ2YTMyZWJkMmZiIiwidW5pb25fbmFtZXNwYWNlIjoidGhlb3J5Y3JhZnQiLCJ1bmlxdWVfZGlzcGxheV9uYW1lIjoiRW1wZXJvciNLaW5nIn0.i06pFYYWvL3dEYh-VPhI7TFPr5xLE_8kYKBSs38408ot5TKWcO2JVHBiiiPG0M7vhERW-8-7zzekUhdtu5kCBNMpozSgIPbarFXzUXm2w9wdndC7ZbCXd0TRW7WpQ7YBUCytgSUp6QTb4COMLuBFZLfLCa-Qah5-jDvBD8AvS89-RBz2EvwoR4IxUi_qKJbQsnO7BOG4mTNETcYiJaS2Fgytu9EUod2r1dfA8W5Ls7AIf7rRL5yEQuCYB48EqmzqWPqqEGomWyXr4RyZBFkjdRWAET1U_APtBRJWRK14RmyyPAAypycpRPj9DIwdmM4taMeOYanxMoQdfYfsIbWOYA
#Basic YmE4ZmI1OWEzNGJiNDgxYWJjYTA4YzQ2YmE0ODgwMjU6
"""headers = {
"Accept": "*/*",
"Accept-Encoding": "gzip",
"x-theorycraft-clientversion": "release0.23.ob-121149-shipping",
"Authorization": "Basic YmE4ZmI1OWEzNGJiNDgxYWJjYTA4YzQ2YmE0ODgwMjU6",
"User-Agent": "Loki/UE5-CL-0 (http-legacy) Windows/10.0.19045.1.768.64bit",
"Content-Length": "0"
}

z = requests.get("https://match-history-jx-prod.prodcluster.awsinfra.theorycraftgames.com/match-history/players/80459d0a0fda4db3b5d25a92aa8a8a09", headers = headers)
print(z)"""

headers = {
"Accept": "*/*",
"Accept-Encoding": "gzip",
"x-theorycraft-clientversion": "release0.23.ob-121149-shipping",
"Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImE5Njg5ZGYxNzVhZWU2OTI1MWY4MDZlNzc4Zjg5MzYwZjNmMjQ0YTMiLCJ0eXAiOiJKV1QifQ.eyJiYW5zIjpbXSwiY2xpZW50X2lkIjoiYmE4ZmI1OWEzNGJiNDgxYWJjYTA4YzQ2YmE0ODgwMjUiLCJjb3VudHJ5IjoiQ0EiLCJkaXNwbGF5X25hbWUiOiJwb3VsaW80NDUyIiwiZXhwIjoxNzQyMjcwNTM3LCJpYXQiOjE3NDIyNjY5MzcsImlzX2NvbXBseSI6dHJ1ZSwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5wcm9qZWN0bG9raS50aGVvcnljcmFmdGdhbWVzLmNvbSIsImpmbGdzIjoxLCJuYW1lc3BhY2UiOiJsb2tpIiwibmFtZXNwYWNlX3JvbGVzIjpbeyJuYW1lc3BhY2UiOiJ0aGVvcnljcmFmdCIsInJvbGVJZCI6IjIyNTE0Mzg4MzllOTQ4ZDc4M2VjMGU1MjgxZGFmMDViIn0seyJuYW1lc3BhY2UiOiJsb2tpIiwicm9sZUlkIjoiMjI1MTQzODgzOWU5NDhkNzgzZWMwZTUyODFkYWYwNWIifV0sInBlcm1pc3Npb25zIjpbXSwicm9sZXMiOltdLCJzY29wZSI6ImFjY291bnQgY29tbWVyY2Ugc29jaWFsIHB1Ymxpc2hpbmcgYW5hbHl0aWNzIiwic3ViIjoiYjQ0NDQ4NDZiNGQxNDMxYjkwYzc5NGIzMzQ4YTFkNDgiLCJ1bmlvbl9pZCI6ImJmMzUzZjhmMTM1OTRiMzhiMmUwZTNlYTUxOTI0ZWM1IiwidW5pb25fbmFtZXNwYWNlIjoidGhlb3J5Y3JhZnQiLCJ1bmlxdWVfZGlzcGxheV9uYW1lIjoiMzM3MjZGNzI2NTcwIzZENDUifQ.qnp85z-j2kI9mmpyM17LMyS9LC06PEh8Ps3H-rvkb4Wo27kfJAHu_pMtVUonE5K3T7-Ada4FUTNZY1HFafk3L3Occ795watOZCNPTDtNkklpfC0dbphEQdQtCoGZ_DIDUN1WetT8R80jujAH6dGWeCUTC5yZp8OVglzlNOneShGDBps6p_IdEEiIpWfzcCqMK1dFHD2RCeZGZCJzjowp2ZZl0DMPlBOYFtaGlycbF5-XkfyOyr7w5qJJB1m1GtikhzY-SkWopwDbfLMKuH72ieiANCPAgqWMjuSkSdJJB4i64EW9ATGXhca4WDiVbdwcDjr4NVXSkhYEbLIwfA_uJw",
"User-Agent": "Loki/UE5-CL-0 (http-legacy) Windows/10.0.19045.1.768.64bit",
"Content-Length": "0"
}
"""
z = requests.get("https://player-stats-jx-prod.prodcluster.awsinfra.theorycraftgames.com/player-stats/players/3131248f6e5a4c64a1a9664135978d95", headers = headers)
print(z.content)
z = requests.get("https://match-history-jx-prod.prodcluster.awsinfra.theorycraftgames.com/match-history/players/b4444846b4d1431b90c794b3348a1d48", headers = headers)
print(z.content)
z = requests.get("https://match-history-jx-prod.prodcluster.awsinfra.theorycraftgames.com/match-history/", headers = headers)
print(z.content)

"""
"""
accepted_players_list = []

z = requests.get("https://supervive.op.gg/api/players/steam-10570b1ecb3a467083a6ef9b005213f4/matches")
#print(z.content)
json_z = z.json()
print(json_z["data"][0]["hero_asset_id"])
print(json_z["data"][1]["hero_asset_id"])
print(json_z["data"][2]["hero_asset_id"])
print(json_z["data"][3]["hero_asset_id"])

z = requests.get("https://supervive.op.gg/api/players/steam-gothcowboy#Jack/id")
#print(z.text)

y = requests.get(f"https://supervive.op.gg/api/matches/steam-20260306-18a2-4086-a87e-34bbe889d66b")
json_y = y.json()
print(json_y[0])
for i in range(len(json_y)):
    print(json_y[i]["player_id_encoded"])
"""
load_dotenv()
print(os.getenv("OLIV_BOT_KEY"))