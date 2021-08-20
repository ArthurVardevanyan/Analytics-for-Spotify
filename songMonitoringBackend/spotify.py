import songMonitoringBackend.playlistSongs as playlistSongs
import songMonitoringBackend.database as database
from songMonitoringBackend.scripts import songIdUpdater
from webBackend.credentials import refresh_token as authorize
import requests
import time
import _thread
import threading
from datetime import datetime, timezone
import os
from django.db import connection
from _datetime import timedelta
import math
import sys
sys.path.append("..")

WORKER = None
THREADS = []
KILL = {}


def modifyThreads(workerCount, user=0):
    with connection.cursor() as cursor:
        global WORKER
        global KILL
        cursor.execute("SELECT COUNT(*) from users where enabled = 1")
        users = cursor.fetchone()[0]
        usersPerWorker = int(math.ceil(users/workerCount))
        usersOnThisWorker = []
        for thread in THREADS:
            usersOnThisWorker.append(thread[0])
        usersOnThisWorker = set(usersOnThisWorker)

        if user != 0:
            sql = "SELECT worker from users WHERE user = '" + \
                str(user) + "'"
            cursor.execute(sql)
            userInfo = cursor.fetchone()[0]
            if userInfo != WORKER:
                KILL['user'] = 1
        if len(usersOnThisWorker) < usersPerWorker:
            users = "SELECT * FROM `users` WHERE `worker` IS NULL and enabled = 1;"
            cursor.execute(users)
            count = len(usersOnThisWorker)

            for user in cursor:
                if count < usersPerWorker:
                    sql = "UPDATE users SET worker = " + \
                        str(WORKER) + " WHERE user = '" + str(user[0]) + "'"
                    cursor.execute(sql)
                    playlistSongThread(user[0])
                    SpotifyThread(user)
                    songIdUpdaterThread(user)
                    time.sleep(1)
                    count += 1
        else:
            for thread in THREADS:
                if thread[0] == user:
                    KILL['user'] = 1
                    sql = "UPDATE users SET worker = NULL WHERE user = '" + \
                        str(user[0]) + "'"
                    cursor.execute(sql)
    return 1


def update_status(user, status, value):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE users SET  `" + status + "` = " +
                       str(value) + " where user ='" + user + "'")


def playlistSongsChecker(user, once=0):
    update_status(user, "statusPlaylist", 0)
    time.sleep(15)
    previousDay = ""
    status = database.user_status(user)
    while(status == 1):
        if (KILL.get(user, 0) == 1):
            break
        update_status(user, "statusPlaylist", 2)
        utc_time = datetime.now()
        local_time = utc_time.astimezone()
        lastUpdated = local_time.strftime("%Y-%m-%d")
        if previousDay != lastUpdated:
            with connection.cursor() as cursor:
                playlists = database.get_playlists(user)
                count = 0
                for playlist in playlists:
                    playlistSongs.main(user, playlist)
                    count = count + 1
                if(count == 0):
                    update_status(user, "statusPlaylist", 0)
                    return
                if(once == 1):
                    update_status(user, "statusPlaylist", 1)
                    return
            previousDay = lastUpdated
            update_status(user, "statusPlaylist", 1)
            time.sleep(3600)
        update_status(user, "statusPlaylist", 1)
        time.sleep(360)
        status = database.user_status(user)
    update_status(user, "statusPlaylist", 0)


def playlistSongThread(user, once=0):
    try:
        print("playlistSongThread: " + user)
        USC = threading.Thread(
            target=playlistSongsChecker, args=(user, once,))
        USC.start()
        thread = [user]
        thread.append(USC)
        global THREADS
        THREADS.append(thread)
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
        thread = [user[0]]
        thread.append(S)
        global THREADS
        THREADS.append(thread)
    except:
        print("Song Thread Failure")


def historySpotify(user):
    try:
        update_status(user, "statusSong", 0)
        time.sleep(10)
        status = database.user_status(user)
        if (status != 1):
            return
        url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
        while(status == 1):
            workerCount = database.scanWorkers(WORKER)
            modifyThreads(workerCount, user)
            global KILL
            if (KILL.get(user, 0) == 1):
                break
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
                                utc_time = datetime.fromisoformat(
                                    listened.get('played_at')[:-5])
                                # https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date/40769643#40769643
                                listened["utc_timestamp"] = utc_time.strftime(
                                    "%Y%m%d%H%M%S")
                                listened["utc_timePlayed"] = utc_time.strftime(
                                    "%Y-%m-%d %H:%M:%S")
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
        if (status != 1):
            return
        url = 'https://api.spotify.com/v1/me/player/currently-playing?market=US'
        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
        previous = " "
        while(status == 1):
            workerCount = database.scanWorkers(WORKER)
            modifyThreads(workerCount, user)
            if (KILL.get(user, 0) == 1):
                break
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


def songIdUpdaterThread(user, once=0):
    try:
        print("songIdUpdaterThread: " + user[0])
        USC = threading.Thread(
            target=songIdUpdaterChecker, args=(user[0], once,))
        USC.start()
        thread = [user[0]]
        thread.append(USC)
        global THREADS
        THREADS.append(thread)
    except Exception as e:
        print(e)
        print("songIdUpdaterThread Thread Failure")


def songIdUpdaterChecker(user, once=0):
    previousDay = ""
    status = database.user_status(user)
    time.sleep(15)
    while(status == 1):
        if (KILL.get(user[0], 0) == 1):
            break
        time.sleep(300)
        utc_time = datetime.now()
        local_time = utc_time.astimezone()
        lastUpdated = local_time.strftime("%Y-%m-%d")
        if previousDay != lastUpdated:
            print(songIdUpdater(user))
            if(once == 1):
                return
            previousDay = lastUpdated
            time.sleep(5000)
        time.sleep(500)
        status = database.user_status(user)


def main():
    with connection.cursor() as cursor:
        global WORKER
        WORKER, workerCount = database.createWorker()
        print("Worker ID: ", WORKER)
        print("Workers  : ", workerCount)
        cursor.execute("SELECT COUNT(*) from users where enabled = 1")
        users = cursor.fetchone()[0]
        print("Users : " + str(users))
        usersPerWorker = int(math.ceil(users/workerCount))
        print("Users Per Worker: " + str(usersPerWorker))
        modifyThreads(workerCount)
    return 1


if __name__ == "__main__":
    main()
