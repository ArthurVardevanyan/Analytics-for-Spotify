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


def user_status(user):
    with connection.cursor() as cursor:
        status = 0
        users = "SELECT * from users where user ='" + user + "'"
        cursor.execute(users)
        for s in cursor:
            status = s[1]
        return status


def update_status(user, status, value):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE users SET  `" + status + "` = " +
                       str(value) + " where user ='" + user + "'")


def unavailableSongsChecker(user):
    update_status(user, "statusPlaylist", 0)
    time.sleep(30)
    previousDay = ""
    status = user_status(user)
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
        status = user_status(user)
    update_status(user, "statusPlaylist", 0)


def unavailableSongThread(user):
    try:
        USC = threading.Thread(
            target=unavailableSongsChecker, args=(user,))
        USC.start()
    except Exception as e:
        print(e)
        print("Playlist Thread Failure")


def historySpotifyThread(user):
    try:
        S = threading.Thread(target=historySpotify, args=(user,))
        S.start()
    except:
        print("Song Thread Failure")


def historySpotify(user):
    try:
        update_status(user, "statusSong", 0)
        time.sleep(30)
        status = user_status(user)
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
                                if(int(timestamp) == song[1]):
                                    listenTemp.append(listened)
                        for listened in response.get("items"):
                            tracked = False
                            for temp in listenTemp:
                                if(listened.get('played_at') == temp.get('played_at')):
                                    tracked = True
                            if(not tracked):
                                print(database.database_input(user, listened))
                update_status(user, "statusSong", 1)
                time.sleep(1200)
            except Exception as e:
                print(e)
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = user_status(user)
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
            historySpotifyThread(user[0])
            time.sleep(1)
    return 1


if __name__ == "__main__":
    main()
