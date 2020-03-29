__version__ = "v20200323"


import requests
from authorization import authorization as authorize
import time
import database
import log

log.logInit("spotify")
print = log.Print
input = log.Input

try:
    url = 'https://api.spotify.com/v1/me/player/currently-playing?market=US'
    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + authorize()}
    previous = " "
    while(True):
        try:
            response = requests.get(url, headers=header)
            if("the access token expired" in str.lower(response.text)):
                header = {"Accept": "application/json",
                          "Content-Type": "application/json", "Authorization": "Bearer " + authorize()}
                response = requests.get(url, headers=header)
            elif("no content" in str.lower(response.reason)):
                print("Nothing is Playing")
                time.sleep(60)
            else:
                response = response.json()
                if(response.get("is_playing")):
                    track = response.get("item").get("name")
                    if(previous != track):
                        if(response.get("item").get("is_local")):
                            response["item"]["id"] = ":" + response.get("item").get("uri").replace("%2C", "").replace(
                                "+", "").replace("%28", "").replace(":", "")[12:30] + response.get("item").get("uri")[-3:]
                        for i in range(0, len(response.get("item").get("artists"))):
                            response["item"]["artists"][i]["id"] = (
                                (":" + (response.get("item").get("artists")[i].get("name"))).zfill(22))[:22]
                        if(int(response.get("progress_ms")) > 30000):
                            print(track)
                            previous = track
                            database.database_input(response)
                            print("Song Counted as Played")
                            time.sleep(25)

                else:
                    print("Nothing is Playing")
                    time.sleep(60)
            time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(60)
except Exception as e:
    print(e)
    time.sleep(60)
