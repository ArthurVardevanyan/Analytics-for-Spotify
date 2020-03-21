__version__ = "v20200320"


import requests
from authorization import authorization as authorize


playlists = ""
try:
    with open("credentials/playlists.txt") as f:
        playlists = f.readlines()
    playlists = [x.strip() for x in playlists]
except:
    print("Credential Failure")


url = 'https://api.spotify.com/v1/playlists/' + playlists[0] + "/tracks"
header = {"Accept": "application/json",
          "Content-Type": "application/json", "Authorization": "Bearer " + authorize()}

playlistSections = []
loop = True
response = requests.get(url, headers=header)
response = response.json()
playlistSections.append(response.get("tracks").get("items"))
if response.get("tracks").get("next") == None:
    loop = False
else:
    url = response.get("tracks").get("next")

while(loop):
    response = requests.get(url, headers=header)
    response = response.json()
    playlistSections.append(response.get("items"))
    if response.get("next") == None:
        loop = False
    else:
        url = response.get("next")


import json
with open('data.json', 'w') as f:
    json.dump(playlistSections, f)
