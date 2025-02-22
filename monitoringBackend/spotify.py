import logging
import webBackend.models as models
import monitoringBackend.playlistSongs as playlistSongs
import monitoringBackend.database as database
from monitoringBackend.scripts import songIdUpdater
from webBackend.credentials import refresh_token as authorize
import requests
import time
import threading
from datetime import datetime, timezone
import math
import sys
sys.path.append("..")

WORKER_HEALTHY=True
WORKER = None
THREADS = []
KILL = {}

log = logging.getLogger(__name__)


def keepAlive():
    """
    Calls Thread Management Function on Loop

    Parameters:
        None
    Returns:
        None
    """
    global WORKER_HEALTHY
    global WORKER
    while(1 == 1):
        time.sleep(75)
        workerCount = database.scanWorkers(WORKER)
        if workerCount == -1:
            WORKER_HEALTHY = False
            log.exception("KeepAlive: DB Error: Skipping")
            continue
        else:
            WORKER_HEALTHY = True
            spawnThreads(workerCount)

def keepAliveThread():
    """
    Calls Function that Spawns a KeepAlive Thread

    Parameters:
        None
    Returns:
        None
    """
    try:
        log.info("keepAlive")
        S = threading.Thread(target=keepAlive)
        S.start()
    except:
        log.exception("keepAlive Thread Failure")


def spawnThreads(workerCount: int):
    """
    Spawn Monitoring Threads for Users.
    Spawns Threads for Users currently not on any workers.

    Parameters:
        workerCount   (int): Worker Count

    Returns:
        int: unused return
    """
    global WORKER
    global KILL
    global THREADS


    if workerCount == -1:
        log.exception("Spawn Threads: DB Error: Skipping")
        return 0

    users = models.Users.objects.filter(enabled=1).count()
    usersPerWorker = int(math.ceil(users/workerCount))
    usersOnThisWorker = []
    for thread in THREADS:
        usersOnThisWorker.append(thread[0])
    usersOnThisWorker = set(usersOnThisWorker)

    if len(usersOnThisWorker) < usersPerWorker:
        log.info("Users On Worker : " + str(len(usersOnThisWorker)))
        log.info("Users Per Worker: " + str(usersPerWorker))
        users = models.Users.objects.filter(enabled=1, worker=None)
        count = len(usersOnThisWorker)

        for user in users:
            if count < usersPerWorker:
                models.Users.objects.filter(
                    user=str(user.user)).update(worker=str(WORKER))
                log.info("Creating User: " + str(user.user))
                playlistSongThread(user.user)
                SpotifyThread(user)
                songIdUpdaterThread(user.user)
                time.sleep(5)
                count += 1
    return 0


def killThreads(workerCount: int, user: str):
    """
    Kills thread of current user if workers are out of balance.

    Parameters:
        workerCount   (int): Worker Count
        user          (str): User ID

    Returns:
        int: unused return
    """
    global WORKER
    global KILL
    global THREADS

    if workerCount == -1:
        log.exception("Kill Threads: DB Error: Skipping")
        return 0

    users = models.Users.objects.filter(enabled=1).count()
    usersPerWorker = int(math.ceil(users/workerCount))
    usersOnThisWorker = []
    for thread in THREADS:
        usersOnThisWorker.append(thread[0])
    usersOnThisWorker = set(usersOnThisWorker)

    userInfo = models.Users.objects.filter(
        user=str(user)).values('worker').first()['worker']
    if userInfo != WORKER:
        log.info("User Doesn't Match Worker")
        newThread = []
        for thread in THREADS:
            if thread[0] == user:
                log.info("Killing: " + str(user))
                KILL[str(user)+"playlistSongThread"] = 1
                KILL[str(user)+"SpotifyThread"] = 1
                KILL[str(user)+"songIdUpdaterThread"] = 1
            else:
                newThread.append(thread)
        THREADS = newThread
        return 0

    if len(usersOnThisWorker) > usersPerWorker:
        log.info("Users On Worker : " + str(len(usersOnThisWorker)))
        log.info("Users Per Worker: " + str(usersPerWorker))
        newThread = []
        for thread in THREADS:
            if thread[0] == user:
                log.info("Killing: " + str(user))
                KILL[str(user)+"playlistSongThread"] = 1
                KILL[str(user)+"SpotifyThread"] = 1
                KILL[str(user)+"songIdUpdaterThread"] = 1
                models.Users.objects.filter(
                    user=str(user)).update(worker=None)
            else:
                newThread.append(thread)
        THREADS = newThread
    return 0


def update_status(user: str, status: str, value: int):
    """
    Kills thread of current user if workers are out of balance.

    Parameters:
        user    (str): User ID
        status  (str): Status Type: (statusPlaylist/statusSong)
        value   (int): 0/1/2

    Returns:
        int: unused return
    """
    if status == "statusPlaylist":
        models.Users.objects.filter(user=str(user)).update(
            statusPlaylist=str(value))
    elif status == "statusSong":
        models.Users.objects.filter(
            user=str(user)).update(statusSong=str(value))
    else:
        return 1
    return 0


def playlistSongsChecker(user: str, once: int = 0):
    """
    Monitors User's Inputted Playlists

    Parameters:
        user    (str): User ID
        once    (str): Optional Flag to Run Once and Exit
    Returns:
        int: unused return
    """
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
    return 0


def playlistSongThread(user: str, once: int = 0):
    """
    Incepts Thread for Monitoring User's Inputted Playlists

    Parameters:
        user    (str): User ID
        once    (str): Optional Flag to Run Once and Exit
    Returns:
        int: unused return
    """
    try:
        log.info("playlistSongThread: " + user)
        USC = threading.Thread(
            target=playlistSongsChecker, args=(user, once,))
        USC.start()
        thread = [user]
        thread.append(USC)
        global THREADS
        THREADS.append(thread)
    except:
        log.exception("Playlist Thread Failure")
    return 0


def SpotifyThread(user: models.Users):
    """
    Incepts Thread for monitoring Spotify User Playback History
    Depending on Flag Defined in Database, either uses
    History Mode, Realtime Mode, or Hybrid Mode.

    Parameters:
        user    (models.Users): User Object
    Returns:
        int: unused return
    """
    try:
        S = []
        if(user.realtime == 1):
            hybrid = False
            log.info("realTimeSpotifyThread: " + user.user)
            S.append(threading.Thread(
                target=realTimeSpotify, args=(user.user, hybrid,)))
        elif(user.realtime == 0):
            log.info("historySpotifyThread: " + user.user)
            S.append(threading.Thread(target=historySpotify, args=(user.user,)))
        elif(user.realtime == 2):
            log.info("hybrid+historySpotifyThread: " + user.user)
            S.append(threading.Thread(target=historySpotify, args=(user.user,)))
            hybrid = True
            log.info("hybrid+realTimeSpotifyThread: " + user.user)
            S.append(threading.Thread(
                target=realTimeSpotify, args=(user.user, hybrid,)))
        global THREADS
        thread = [user.user]
        S[0].start()
        thread.append(S[0])
        THREADS.append(thread)
        if len(S) > 1:
            thread = [user.user]
            S[1].start()
            thread.append(S[1])
            THREADS.append(thread)
    except:
        log.exception("Song Thread Failure")
    return 0


def historySpotify(user: str):
    """
    Incepts Thread for Monitoring User's Playback History using History Mode

    Parameters:
        user    (str): User ID
    Returns:
        int: unused return
    """
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
                    newSongs = False
                    response = response.json()
                    listeningHistory = models.ListeningHistory.objects.filter(
                        user=str(user)).values('timestamp').order_by('-timePlayed')[0:50]

                    listenTemp = []
                    for song in listeningHistory:
                        for listened in response.get("items"):
                            utc_time = datetime.fromisoformat(
                                listened.get('played_at').split(".")[0].replace("Z", ""))
                            timestamp = utc_time.strftime("%Y%m%d%H%M%S")
                            # https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date/40769643#40769643
                            listened["utc_timestamp"] = utc_time.strftime(
                                "%Y%m%d%H%M%S")
                            listened["utc_timePlayed"] = utc_time.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            if(int(timestamp) == song['timestamp']):
                                listenTemp.append(listened)
                    for listened in response.get("items"):
                        tracked = False
                        for temp in listenTemp:
                            if(listened.get('played_at') == temp.get('played_at')):
                                tracked = True
                        if(not tracked):
                            utc_time = datetime.fromisoformat(
                                listened.get('played_at').split(".")[0].replace("Z", ""))
                            # https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date/40769643#40769643
                            listened["utc_timestamp"] = utc_time.strftime(
                                "%Y%m%d%H%M%S")
                            listened["utc_timePlayed"] = utc_time.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            listened["item"] = listened.get("track")
                            log.info("History: " + str(user) + ": " +
                                     database.database_input(user, listened).get("track").get("name"))
                            newSongs = True
                    if (newSongs == False):
                        log.debug("No New Songs: " + str(user))
                update_status(user, "statusSong", 1)
                time.sleep(1200)
            except:
                log.exception("Song Lookup Failure: " + str(user))
                log.warning(str(response))
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = database.user_status(user)
    except:
        log.exception("History Song Failure: " + str(user))
        update_status(user, "statusSong", 1)
        time.sleep(60)
    update_status(user, "statusSong", 0)
    return 0


def realTimeSpotify(user: str, hybrid: bool):
    """
    Incepts Thread for Monitoring User's Playback History using RealTime Mode

    Parameters:
        user    (str): User ID
        hybrid  (bool): Flag whether hybrid scanning mode is enabled or not.
    Returns:
        int: unused return
    """
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
                    log.debug("Nothing is Playing: " + str(user))
                    update_status(user, "statusSong", 1)
                    time.sleep(60)
                elif(response.json().get("is_playing") and
                     "ad" in str.lower(response.json().get("currently_playing_type", "false"))):
                    log.debug("Ignoring Ad: " + str(user))
                    update_status(user, "statusSong", 1)
                    time.sleep(30)
                elif(response.json().get("is_playing") and
                     "episode" in str.lower(response.json().get("currently_playing_type", "false"))):
                    log.debug("Ignoring Podcast: " + str(user))
                    update_status(user, "statusSong", 1)
                    time.sleep(90)
                elif(response.json().get("is_playing") and
                     "unknown" in str.lower(response.json().get("currently_playing_type", "false"))):
                    log.warning("Unknown Error: " +
                                str(user) + " : " + str(response.json()))
                    update_status(user, "statusSong", 1)
                    time.sleep(45)
                else:
                    response = response.json()
                    if(response.get("is_playing")):
                        if(response.get("item").get("is_local") == False and hybrid == True):
                            log.debug("Hybrid Mode: " + str(user) +
                                      ": Local Song Not Playing")
                            update_status(user, "statusSong", 1)
                            time.sleep(60)
                        else:
                            track = response.get("item").get("name")
                            if(previous != track):
                                if(response.get("item").get("is_local")):
                                    response["item"]["id"] = ":" + response.get("item").get("uri").replace("%2C", "").replace(
                                        "+", "").replace("%28", "").replace(":", "")[12:30] + response.get("item").get("uri")[-3:]
                                    for i in range(0, len(response.get("item").get("artists"))):
                                        response["item"]["artists"][i]["id"] = (
                                            (":" + (response.get("item").get("artists")[i].get("name"))).zfill(22))[:22]
                                if(int(response.get("progress_ms")) > 30000):
                                    previous = track
                                    utc_time = datetime.fromtimestamp(
                                        response.get('timestamp')/1000, timezone.utc)
                                    response["utc_timestamp"] = utc_time.strftime(
                                        "%Y%m%d%H%M%S")
                                    response["utc_timePlayed"] = utc_time.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    database.database_input(user, response)
                                    log.debug(
                                        "Song Counted as Played: " + str(track))
                                    update_status(user, "statusSong", 1)
                                    time.sleep(25)
                            if(int(response.get("progress_ms")) > 30000):
                                time.sleep(10)
                    else:
                        log.debug("Nothing is Playing: " + str(user))
                        update_status(user, "statusSong", 1)
                        time.sleep(60)
                update_status(user, "statusSong", 1)
                time.sleep(5)
            except:
                log.exception("Song Lookup Failure: " + str(user))
                log.warning(str(response))
                update_status(user, "statusSong", 1)
                time.sleep(60)
            status = database.user_status(user)
    except:
        log.exception("Realtime Song Failure: " + str(user))
        update_status(user, "statusSong", 1)
        time.sleep(60)
    update_status(user, "statusSong", 0)
    return 0


def songIdUpdaterThread(user: str, once: int = 0):
    """
    Incepts Thread for Updating Song IDs

    Parameters:
        user    (str): User ID
        once    (str): Optional Flag to Run Once and Exit
    Returns:
        int: unused return
    """
    try:
        log.info("songIdUpdaterThread: " + user)
        USC = threading.Thread(
            target=songIdUpdaterChecker, args=(user, once,))
        USC.start()
        thread = [user]
        thread.append(USC)
        global THREADS
        THREADS.append(thread)
    except:
        log.exception("songIdUpdaterThread Thread Failure")


def songIdUpdaterChecker(user: str, once: int = 0):
    """
    Thread for Monitoring when SongIDs have changed from Spotify.

    Parameters:
        user    (str): User ID
        once    (str): Optional Flag to Run Once and Exit
    Returns:
        int: unused return
    """
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
            changeHistory = songIdUpdater(user)
            if changeHistory:
                log.info(str(changeHistory))
            if(once == 1):
                return
            previousDay = lastUpdated
            time.sleep(5000)
        time.sleep(500)
        status = database.user_status(user)


def boot():
    """
    Boots the Spotify Monitoring Backend.
    Assigns this Instance an UID into the Database
    Logs some Startup Information

    Parameters:
        None
    Returns:
        int: unused return
    """
    global WORKER
    WORKER = database.createWorker()
    workerCount = database.scanWorkers(WORKER)
    log.info("Worker ID: " + str(WORKER))
    log.info("Workers  : " + str(workerCount))
    users = models.Users.objects.filter(enabled=1).count()
    log.info("Users : " + str(users))
    usersPerWorker = int(math.ceil(users/workerCount))
    log.info("Users Per Worker: " + str(usersPerWorker))
    return 0


def main():
    """
    Spotify Monitoring Backend EntryPoint

    Parameters:
        None
    Returns:
        int: unused return
    """
    boot()
    keepAliveThread()
    return 0


if __name__ == "__main__":
    main()
