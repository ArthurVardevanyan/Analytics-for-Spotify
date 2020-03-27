__version__ = "v20200320"

import mysql.connector
import json
from datetime import datetime, timezone


def add_artists(spotify, cursor):
    artists = "SELECT * from artists"
    cursor.execute(artists)
    artists = []
    for (id) in cursor:
        artists.append(id[0])
    for iter in spotify.get("item").get("artists"):
        exists = False
        for i in artists:
            if iter.get("id") == i:
                exists = True
        if not exists:
            add_artist = ("INSERT INTO artists"
                          "(id,name)"
                          "VALUES (%s, %s)")
            data_artist = (
                iter.get("id"),
                iter.get("name")
            )
            cursor.execute(add_artist, data_artist)


def add_song_artists(spotify, cursor):

    for iter in spotify.get("item").get("artists"):
        add_song_artist = ("INSERT INTO songArtists"
                           "(songID,artistID)"
                           "VALUES (%s, %s)")
        data_song_artist = (
            spotify.get("item").get("id"),
            iter.get("id")
        )
        cursor.execute(add_song_artist, data_song_artist)


def add_song(spotify, cursor):
    playCount = "SELECT `playCount` from `songs` where `id` = '" + \
        spotify.get("item").get("id") + "'"

    cursor.execute(playCount)
    playCount = 0
    for (id) in cursor:
        playCount = int(id[0])
    if playCount == 0:
        add_song = ("INSERT IGNORE INTO songs"
                    "(id,name,trackLength)"
                    "VALUES (%s, %s, %s)")
        data_song = (
            spotify.get("item").get("id"),
            spotify.get("item").get("name"),
            spotify.get("item").get("duration_ms"),
        )
        cursor.execute(add_song, data_song)
        add_song_artists(spotify, cursor)  # Function
    else:
        playCount = playCount + 1
        add_song = ("UPDATE songs SET playCount = '" + str(playCount) +
                    "' WHERE id = '" + spotify.get("item").get("id") + "'")
        cursor.execute(add_song)


def listenting_history(spotify, cursor):
    # https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date/40769643#40769643
    utc_time = datetime.fromtimestamp(
        spotify.get('timestamp')/1000, timezone.utc)
    local_time = utc_time.astimezone()
    timestamp = local_time.strftime("%Y%m%d%H%M%S")
    timePlayed = local_time.strftime("%Y-%m-%d %H:%M:%S")

    add_play = ("INSERT  INTO listeningHistory"
                "(timestamp,timePlayed, songID,json)"
                "VALUES (%s, %s, %s, %s)")
    data_play = (
        timestamp,
        timePlayed,
        spotify.get("item").get("id"),
        json.dumps(spotify)
    )
    cursor.execute(add_play, data_play)


def database_input(spotify):

    try:
        with open("credentials/databaseCredentials.txt") as f:
            cred = f.readlines()
        cred = [x.strip() for x in cred]
    except:
        print("Credential Failure")

    db = mysql.connector.connect(
        host="localhost",
        user=cred[0],
        passwd=cred[1],
        database=cred[2],
        auth_plugin='mysql_native_password'
    )

    cursor = db.cursor()

    add_artists(spotify, cursor)
    add_song(spotify, cursor)
    listenting_history(spotify, cursor)

    db.commit()
    db.close

    return 1
