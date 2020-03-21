__version__ = "v20200320"


import requests
from authorization import authorization as authorize
import time
import database

url = 'https://api.spotify.com/v1/me/player/currently-playing?market=ES'
header = {"Accept": "application/json",
          "Content-Type": "application/json", "Authorization": "Bearer " + authorize()}
previous =" "
while(True):
    
    response = requests.get(url, headers=header)
    response = response.json()
    track = response.get("item").get("name")
    if(not response.get("is_local")):
        if(previous != track):
            if(int(response.get("progress_ms")) > 30000):
                print(track)
                previous = track
                print("Song Counted as Played")   
                database.database_input(response)  
    time.sleep(1)
