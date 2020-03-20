__version__ = "v20200320"


import requests
from authorization import authorization as authorize
import time

url = 'https://api.spotify.com/v1/me/player/currently-playing?market=ES'
header = {"Accept": "application/json",
          "Content-Type": "application/json", "Authorization": "Bearer " + authorize()}

while(True):
    response = requests.get(url, headers=header)
    response = response.json()
    track = response.get("item").get("name")
    print(track)
    time.sleep(1)
