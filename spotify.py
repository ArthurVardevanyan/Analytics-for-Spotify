import requests
from analytics.views import refresh_token as authorize
import time
import database
import log
import unavailableSongs
import _thread
import threading
from datetime import datetime, timezone
import os
import glob
from django.db import connection
from _datetime import timedelta

os.chdir(os.path.abspath(os.path.dirname(__file__)))
log.logInit("spotify")
print = log.Print
input = log.Input


def file_list():
    # Grabs the PDF's in the requested order
    fileList = sorted(
        glob.glob(".cache-*"))
    # Strips the file path data to leave just the filename
    Stripped_List = [os.path.basename(x) for x in fileList]
    return Stripped_List  # Returns the Stripped List to Main Function


def update_status(user, status, value):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE users SET  `" + status + "` = " +
                       str(value) + " where user ='" + user + "'")


def unavailableSongsChecker(user):
    update_status(user, "statusPlaylist", 0)
    time.sleep(30)
    previousDay = ""
    status = database.user_status(user)
    while(status):
        update_status(user, "statusPlaylist", 2)
        utc_time = datetime.now()
        local_time = utc_time.astimezone()
        lastUpdated = local_time.strftime("%Y-%m-%d")
        if previousDay != lastUpdated:
            unavailableSongs.main(user)
            previousDay = lastUpdated
            update_status(user, "statusPlaylist", 1)
            time.sleep(3600)
        update_status(user, "statusPlaylist", 1)
        time.sleep(360)
        status = database.user_status(user)
    update_status(user, "statusPlaylist", 0)


def unavailableSongThread(user):
    try:
        print("unavailableSongThread: " + user)
        USC = threading.Thread(
            target=unavailableSongsChecker, args=(user,))
        USC.start()
    except Exception as e:
        print(e)
        print("Playlist Thread Failure")


def SpotifyThread(user):
    try:
        if(user[5]):
            print("realTimeSpotifyThread: " + user[0])
            S = threading.Thread(target=realTimeSpotify, args=(user[0],))
        else:
            print("historySpotifyThread: " + user[0])
            S = threading.Thread(target=historySpotify, args=(user[0],))
        S.start()
    except:
        print("Song Thread Failure")


def historySpotify(user):
    try:
        update_status(user, "statusSong", 0)
        time.sleep(10)
        status = database.user_status(user)
        if (not status):
            return
        url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"

        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
        previous = " "
        while(status):
            update_status(user, "statusSong", 2)
            try:
                response = requests.get(url, headers=header)
                if("the access token expired" in str.lower(response.text)):
                    header = {"Accept": "application/json",
                              "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
                    response = requests.get(url, headers=header)
                else:
                    response = response.json()
                    query = "SELECT * FROM `listeningHistory`  where user ='" + user + \
                        "' ORDER BY `listeningHistory`.`timePlayed`  DESC  LIMIT 50"
                    listeningHistoy = []
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                        listenTemp = []
                        for song in cursor:
                            for listened in response.get("items"):
                                utc_time = datetime.fromisoformat(
                                    listened.get('played_at')[:-5])
                                timestamp = utc_time.strftime("%Y%m%d%H%M%S")
                                # https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date/40769643#40769643
                                listened["utc_timestamp"] = utc_time.strftime(
                                    "%Y%m%d%H%M%S")
                                listened["utc_timePlayed"] = utc_time.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                                if(int(timestamp) == song[1]):
                                    listenTemp.append(listened)
                        for listened in response.get("items"):
                            tracked = False
                            for temp in listenTemp:
                                if(listened.get('played_at') == temp.get('played_at')):
                                    tracked = True
                            if(not tracked):
                                listened["item"] = listened.get("track")
                                print(database.database_input(
                                    user, listened).get("track").get("name"))
                update_status(user, "statusSong", 1)
                time.sleep(1200)
            except Exception as e:
                print(e)
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = database.user_status(user)
    except Exception as e:
        print(e)
        update_status(user, "statusSong", 1)
        time.sleep(60)
    update_status(user, "statusSong", 0)


def realTimeSpotify(user):
    try:
        update_status(user, "statusSong", 0)
        time.sleep(10)
        status = database.user_status(user)
        if (not status):
            return
        url = 'https://api.spotify.com/v1/me/player/currently-playing?market=US'
        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
        previous = " "
        while(status):
            update_status(user, "statusSong", 2)
            try:
                response = requests.get(url, headers=header)
                if("the access token expired" in str.lower(response.text)):
                    header = {"Accept": "application/json",
                              "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
                    response = requests.get(url, headers=header)
                elif("no content" in str.lower(response.reason)):
                    print("Nothing is Playing")
                    update_status(user, "statusSong", 1)
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
                                utc_time = datetime.fromtimestamp(
                                    response.get('timestamp')/1000, timezone.utc)
                                response["utc_timestamp"] = utc_time.strftime(
                                    "%Y%m%d%H%M%S")
                                response["utc_timePlayed"] = utc_time.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                                database.database_input(user, response)
                                print("Song Counted as Played")
                                update_status(user, "statusSong", 1)
                                time.sleep(25)

                    else:
                        print("Nothing is Playing")
                        update_status(user, "statusSong", 1)
                        time.sleep(60)
                update_status(user, "statusSong", 1)
                time.sleep(3)
            except Exception as e:
                print(e)
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = database.user_status(user)
    except Exception as e:
        print(e)
        update_status(user, "statusSong", 1)
        time.sleep(60)
    update_status(user, "statusSong", 0)


def main():
    with connection.cursor() as cursor:
        users = "SELECT * from users"
        cursor.execute(users)
        for user in cursor:
            unavailableSongThread(user[0])
            SpotifyThread(user)
            time.sleep(1)
    return 1


if __name__ == "__main__":
    main()
