__version__ = "v20200320"


import requests

key = ""
try:
    with open("Credentials/spotifyToken.txt") as f:
        key = f.readlines()
    key = [x.strip() for x in key]
    key = str(key[0])
except:
    print("Credential Failure")

url = 'https://api.spotify.com/v1/me/player/currently-playing?market=ES'
header = {"Accept": "application/json",
          "Content-Type": "application/json", "Authorization": "Bearer " + key}

response = requests.get(url, headers=header)
response = response.json()
track = response.get("item").get("name")
print(track)
