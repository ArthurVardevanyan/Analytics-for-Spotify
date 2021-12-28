import json
from datetime import datetime, timezone
from django.db import connection
import sys
from random import randint
import logging
import sys
sys.path.append("..")

log = logging.getLogger(__name__)


def scanWorkers(workerID):
    with connection.cursor() as cursor:
        utc_time = datetime.now()
        currentEpoch = int(utc_time.astimezone().timestamp())
        time = utc_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE workers SET lastUpdated = " + \
            str(currentEpoch) + " WHERE worker = " + str(workerID)
        cursor.execute(sql)
        sql = "UPDATE workers SET updatedTime = '" + \
            str(time) + "' WHERE worker = " + str(workerID)
        cursor.execute(sql)
        cursor.execute("SELECT * from workers")
        count = 0
        for worker in cursor:
            if currentEpoch - worker[1] > 90:
                from webBackend.models import Workers
                Workers.objects.filter(worker=str(worker[0])).delete()

            else:
                count += 1
    return count


def createWorker():

    workerID = randint(10**(9-1), (10**9)-1)
    utc_time = datetime.now()
    currentEpoch = int(utc_time.astimezone().timestamp())
    time = utc_time.strftime("%Y-%m-%d %H:%M:%S")

    add_worker = ("INSERT INTO workers"
                  "(worker,lastUpdated,creationTime,updatedTime)"
                  "VALUES (%s, %s, %s, %s)")
    data_worker = (
        workerID,
        currentEpoch,
        time,
        time
    )
    with connection.cursor() as cursor:
        cursor.execute(add_worker, data_worker)

    count = scanWorkers(workerID)
    return workerID, count


def user_status(user, detailed=0):
    with connection.cursor() as cursor:
        users = "SELECT * from users where user ='" + user + "'"
        cursor.execute(users)
        if(detailed):
            for s in cursor:
                return s
        else:
            status = 0
            for s in cursor:
                status = s[1]
            return status


def add_artists(spotify, cursor):
    artists = "SELECT * from artists"
    cursor.execute(artists)
    artists = []
    for id in cursor:
        artists.append(id[0])
    for iter in spotify.get("item").get("artists"):
        exists = False
        for i in artists:
            if iter.get("id") == i:
                exists = True
        if not exists:
            data_artist = (
                iter.get("id"),
                iter.get("name")
            )
            add_artist = ("INSERT IGNORE INTO artists"
                          "(id,name)"
                          "VALUES (%s, %s)")
            data_artist = (
                iter.get("id"),
                iter.get("name")
            )
            cursor.execute(add_artist, data_artist)


def add_song_artists(spotify, cursor):

    for iter in spotify.get("item").get("artists"):
        add_song_artist = ("INSERT IGNORE INTO songArtists"
                           "(songID,artistID)"
                           "VALUES (%s, %s)")
        data_song_artist = (
            spotify.get("item").get("id"),
            iter.get("id")
        )
        cursor.execute(add_song_artist, data_song_artist)


def add_song_count(user, spotify, cursor, count=1):
    playCount = "SELECT `playCount` from `playcount` WHERE songID = '" + \
        spotify.get("item").get("id") + "' and  user = '" + user + "'"
    cursor.execute(playCount)
    playCount = -1
    for id in cursor:
        playCount = int(id[0])
    if playCount < 0:
        add_song = ("INSERT IGNORE INTO playcount "
                    "(user,songID,playCount) "
                    "VALUES (%s, %s, %s)")
        data_song = (
            user,
            spotify.get("item").get("id"),
            count,
        )
        cursor.execute(add_song, data_song)
        add_song_artists(spotify, cursor)  # Function
    else:
        playCount = playCount + count
        add_song = ("UPDATE playcount SET playCount = '" + str(playCount) +
                    "' WHERE songID = '" + spotify.get("item").get("id") + "' and  user = '" + user + "'")
        cursor.execute(add_song)


def add_song(spotify, cursor):
    add_song = ("INSERT IGNORE INTO songs"
                "(id,name,trackLength)"
                "VALUES (%s, %s, %s)")
    data_song = (
        spotify.get("item").get("id"),
        spotify.get("item").get("name"),
        spotify.get("item").get("duration_ms")
    )
    cursor.execute(add_song, data_song)
    add_song_artists(spotify, cursor)  # Function


def listening_history(user, spotify, cursor):

    add_play = ("INSERT IGNORE INTO listeningHistory"
                "(user, timestamp,timePlayed, songID)"
                "VALUES (%s, %s, %s, %s)")
    data_play = (
        user,
        spotify.get('utc_timestamp'),
        spotify.get('utc_timePlayed'),
        spotify.get("item").get("id"),
    )
    cursor.execute(add_play, data_play)

    if (int(cursor.rowcount) == 0):
        logging.warning("Duplicate History Song: " + str(data_play[:-1]))
        return 0
    return 1


def get_playlists(user):
    with connection.cursor() as cursor:
        query = "SELECT playlists.playlistID, name, playlists.lastUpdated from playlists  INNER JOIN playlistsUsers ON playlistsUsers.playlistID = playlists.playlistID    where user = '"+user+"'"
        cursor.execute(query)
        playlists = []
        for playlist in cursor:
            playlists.append((playlist[0], playlist[1], playlist[2]))
        return playlists


def add_playlist(user, playlist):
    with connection.cursor() as cursor:
        utc_time = datetime.utcnow()
        lastUpdated = utc_time.strftime("%Y-%m-%d %H:%M:%S")

        sql = "DELETE FROM playlistSongs WHERE playlistID = '" + \
            playlist+"'"
        cursor.execute(sql)

        addPlaylist = " UPDATE playlists SET lastUpdated = '"+lastUpdated+"' WHERE playlistID = '" + \
            playlist+"'"
        cursor.execute(addPlaylist)


def add_playlist_songs(cursor, song, playlist, status):
    addPlaylist = ("INSERT IGNORE INTO  playlistSongs"
                   "(playlistID, songID, songStatus)"
                   "VALUES (%s, %s, %s)")
    dataPlaylist = (
        playlist,
        song.get("item").get("id"),
        status
    )
    cursor.execute(addPlaylist, dataPlaylist)

    if (int(cursor.rowcount) == 0):
        logging.warning("Duplicate Playlist Song: " + str(dataPlaylist))


def database_input(user, spotify):
    with connection.cursor() as cursor:
        add_artists(spotify, cursor)
        add_song(spotify, cursor)
        if(listening_history(user, spotify, cursor)):
            add_song_count(user, spotify, cursor)
    return spotify


def playlist_input(user, spotify, playlist, status):
    with connection.cursor() as cursor:
        spotify["item"] = spotify.get("track")
        if(spotify.get("item").get("is_local")):
            spotify["item"]["id"] = ":" + spotify.get("item").get("uri").replace("%2C", "").replace(
                "+", "").replace("%28", "").replace(":", "")[12:30] + spotify.get("item").get("uri")[-3:]
            for i in range(0, len(spotify.get("item").get("artists"))):
                spotify["item"]["artists"][i]["id"] = (
                    (":" + (spotify.get("item").get("artists")[i].get("name"))).zfill(22))[:22]
        add_artists(spotify, cursor)
        add_song(spotify, cursor)
        add_song_count(user, spotify, cursor, 0)
        add_playlist_songs(cursor, spotify,  playlist, status)
    return 1
