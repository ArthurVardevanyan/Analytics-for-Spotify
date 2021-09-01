import logging
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

logger = logging.getLogger(__name__)


def keepAlive():
    global WORKER
    while(1 == 1):
        time.sleep(75)
        spawnThreads(database.scanWorkers(WORKER))


def keepAliveThread():
    try:
        logger.info("keepAlive")
        S = threading.Thread(target=keepAlive)
        S.start()
    except:
        logger.exception("keepAlive Thread Failure")


def spawnThreads(workerCount):
    with connection.cursor() as cursor:
        global WORKER
        global KILL
        global THREADS
        cursor.execute("SELECT COUNT(*) from users where enabled = 1")
        users = cursor.fetchone()[0]
        usersPerWorker = int(math.ceil(users/workerCount))
        usersOnThisWorker = []
        for thread in THREADS:
            usersOnThisWorker.append(thread[0])
        usersOnThisWorker = set(usersOnThisWorker)

        if len(usersOnThisWorker) < usersPerWorker:
            logger.info("Users On Worker : " + str(len(usersOnThisWorker)))
            logger.info("Users Per Worker: " + str(usersPerWorker))
            users = "SELECT * FROM `users` WHERE `worker` IS NULL and enabled = 1;"
            cursor.execute(users)
            count = len(usersOnThisWorker)

            for user in cursor:
                if count < usersPerWorker:
                    sql = "UPDATE users SET worker = " + \
                        str(WORKER) + " WHERE user = '" + str(user[0]) + "'"
                    cursor.execute(sql)
                    logger.info("Creating User: " + str(user[0]))
                    playlistSongThread(user[0])
                    SpotifyThread(user)
                    songIdUpdaterThread(user)
                    time.sleep(5)
                    count += 1
    return 1


def killThreads(workerCount, user):
    with connection.cursor() as cursor:
        global WORKER
        global KILL
        global THREADS
        cursor.execute("SELECT COUNT(*) from users where enabled = 1")
        users = cursor.fetchone()[0]
        usersPerWorker = int(math.ceil(users/workerCount))
        usersOnThisWorker = []
        for thread in THREADS:
            usersOnThisWorker.append(thread[0])
        usersOnThisWorker = set(usersOnThisWorker)

        cursor.execute(
            "SELECT worker from users WHERE user = '" + str(user) + "'")
        userInfo = cursor.fetchone()[0]
        if userInfo != WORKER:
            logger.info("User Doesn't Match Worker")
            newThread = []
            for thread in THREADS:
                if thread[0] == user:
                    logger.info("Killing: " + str(user))
                    KILL[str(user)+"playlistSongThread"] = 1
                    KILL[str(user)+"SpotifyThread"] = 1
                    KILL[str(user)+"songIdUpdaterThread"] = 1
                else:
                    newThread.append(thread)
            THREADS = newThread
            return 1

        if len(usersOnThisWorker) > usersPerWorker:
            logger.info("Users On Worker : " + str(len(usersOnThisWorker)))
            logger.info("Users Per Worker: " + str(usersPerWorker))
            newThread = []
            for thread in THREADS:
                if thread[0] == user:
                    logger.info("Killing: " + str(user))
                    KILL[str(user)+"playlistSongThread"] = 1
                    KILL[str(user)+"SpotifyThread"] = 1
                    KILL[str(user)+"songIdUpdaterThread"] = 1
                    sql = "UPDATE users SET worker = NULL WHERE user = '" + \
                        str(user) + "'"
                    cursor.execute(sql)
                else:
                    newThread.append(thread)
            THREADS = newThread
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
        global KILL
        if (KILL.get(user+"playlistSongThread", 0) == 1):
            del KILL[str(user)+"playlistSongThread"]
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
        logger.info("playlistSongThread: " + user)
        USC = threading.Thread(
            target=playlistSongsChecker, args=(user, once,))
        USC.start()
        thread = [user]
        thread.append(USC)
        global THREADS
        THREADS.append(thread)
    except:
        logger.exception("Playlist Thread Failure")


def SpotifyThread(user):
    try:
        if(user[5]):
            logger.info("realTimeSpotifyThread: " + user[0])
            S = threading.Thread(target=realTimeSpotify, args=(user[0],))
        else:
            logger.info("historySpotifyThread: " + user[0])
            S = threading.Thread(target=historySpotify, args=(user[0],))
        S.start()
        thread = [user[0]]
        thread.append(S)
        global THREADS
        THREADS.append(thread)
    except:
        logger.exception("Song Thread Failure")


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
            killThreads(workerCount, user)
            global KILL
            if (KILL.get(user+"SpotifyThread", 0) == 1):
                del KILL[str(user)+"SpotifyThread"]
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
                                logger.info(database.database_input(
                                    user, listened).get("track").get("name"))
                update_status(user, "statusSong", 1)
                time.sleep(1200)
            except:
                logger.exception("Song Lookup Failure")
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = database.user_status(user)
    except:
        logger.exception("History Song Failure")
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
            killThreads(workerCount, user)
            global KILL
            if (KILL.get(user+"SpotifyThread", 0) == 1):
                del KILL[str(user)+"SpotifyThread"]
                break
            update_status(user, "statusSong", 2)
            try:
                response = requests.get(url, headers=header)
                if("the access token expired" in str.lower(response.text)):
                    header = {"Accept": "application/json",
                              "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
                    response = requests.get(url, headers=header)
                elif("no content" in str.lower(response.reason)):
                    logger.info("Nothing is Playing")
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
                                logger.info(track)
                                previous = track
                                utc_time = datetime.fromtimestamp(
                                    response.get('timestamp')/1000, timezone.utc)
                                response["utc_timestamp"] = utc_time.strftime(
                                    "%Y%m%d%H%M%S")
                                response["utc_timePlayed"] = utc_time.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                                database.database_input(user, response)
                                logger.info("Song Counted as Played")
                                update_status(user, "statusSong", 1)
                                time.sleep(25)
                    else:
                        logger.info("Nothing is Playing")
                        update_status(user, "statusSong", 1)
                        time.sleep(60)
                update_status(user, "statusSong", 1)
                time.sleep(3)
            except:
                logger.exception("song Lookup Failure")
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = database.user_status(user)
    except:
        logger.exception("Realtime Song Failure")
        update_status(user, "statusSong", 1)
        time.sleep(60)
    update_status(user, "statusSong", 0)


def songIdUpdaterThread(user, once=0):
    try:
        logger.info("songIdUpdaterThread: " + user[0])
        USC = threading.Thread(
            target=songIdUpdaterChecker, args=(user[0], once,))
        USC.start()
        thread = [user[0]]
        thread.append(USC)
        global THREADS
        THREADS.append(thread)
    except:
        logger.exception("songIdUpdaterThread Thread Failure")


def songIdUpdaterChecker(user, once=0):
    previousDay = ""
    status = database.user_status(user)
    time.sleep(15)
    while(status == 1):
        global KILL
        if (KILL.get(user+"songIdUpdaterThread", 0) == 1):
            del KILL[str(user)+"songIdUpdaterThread"]
            break
        time.sleep(300)
        utc_time = datetime.now()
        local_time = utc_time.astimezone()
        lastUpdated = local_time.strftime("%Y-%m-%d")
        if previousDay != lastUpdated:
            logger.info(songIdUpdater(user))
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
        logger.info("Worker ID: " + str(WORKER))
        logger.info("Workers  : " + str(workerCount))
        cursor.execute("SELECT COUNT(*) from users where enabled = 1")
        users = cursor.fetchone()[0]
        logger.info("Users : " + str(users))
        usersPerWorker = int(math.ceil(users/workerCount))
        logger.info("Users Per Worker: " + str(usersPerWorker))
        keepAliveThread()
    return 1


if __name__ == "__main__":
    main()
