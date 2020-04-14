import mysql.connector
import json
from datetime import datetime, timezone


def credentials():
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
    return db


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


def add_song(spotify, cursor, count=1):
    playCount = "SELECT `playCount` from `songs` where `id` = '" + \
        spotify.get("item").get("id") + "'"

    cursor.execute(playCount)
    playCount = -1
    for (id) in cursor:
        playCount = int(id[0])
    if playCount < 0:
        add_song = ("INSERT IGNORE INTO songs"
                    "(id,name,playCount,trackLength)"
                    "VALUES (%s, %s, %s, %s)")
        data_song = (
            spotify.get("item").get("id"),
            spotify.get("item").get("name"),
            count,
            spotify.get("item").get("duration_ms")
        )
        cursor.execute(add_song, data_song)
        add_song_artists(spotify, cursor)  # Function
    else:
        playCount = playCount + count
        add_song = ("UPDATE songs SET playCount = '" + str(playCount) +
                    "' WHERE id = '" + spotify.get("item").get("id") + "'")
        cursor.execute(add_song)


def listenting_history(spotify, cursor):
    # https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date/40769643#40769643
    utc_time = datetime.fromtimestamp(
        spotify.get('timestamp')/1000, timezone.utc)
    timestamp = utc_time.strftime("%Y%m%d%H%M%S")
    timePlayed = utc_time.strftime("%Y-%m-%d %H:%M:%S")

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


def add_playlist(playlist):
    utc_time = datetime.utcnow()
    lastUpdated = utc_time.strftime("%Y-%m-%d %H:%M:%S")
    db = credentials()
    cursor = db.cursor()

    sql = "DELETE FROM playlistSongs WHERE playlistID = '" + \
        playlist.get("id")+"'"
    cursor.execute(sql)
    sql = "DELETE FROM playlists WHERE id = '"+playlist.get("id")+"'"
    cursor.execute(sql)

    addPlaylist = ("INSERT IGNORE INTO playlists"
                   "(id,name, lastUpdated)"
                   "VALUES (%s, %s, %s)")
    dataPlaylist = (
        playlist.get("id"),
        playlist.get("name"),
        lastUpdated
    )
    cursor.execute(addPlaylist, dataPlaylist)

    db.commit()
    db.close


def add_playlist_songs(cursor, song, playlist, status):
    addPlaylist = ("INSERT IGNORE INTO  playlistSongs"
                   "(playlistID, songID, songStatus)"
                   "VALUES (%s, %s, %s)")
    dataPlaylist = (
        playlist.get("id"),
        song.get("item").get("id"),
        status
    )
    cursor.execute(addPlaylist, dataPlaylist)


def database_input(spotify):

    db = credentials()
    cursor = db.cursor()
    add_artists(spotify, cursor)
    add_song(spotify, cursor)
    listenting_history(spotify, cursor)
    db.commit()
    db.close


def playlist_input(spotify, playlist, status):
    db = credentials()
    cursor = db.cursor()
    spotify["item"] = spotify.get("track")
    if(spotify.get("item").get("is_local")):
        spotify["item"]["id"] = ":" + spotify.get("item").get("uri").replace("%2C", "").replace(
            "+", "").replace("%28", "").replace(":", "")[12:30] + spotify.get("item").get("uri")[-3:]
        for i in range(0, len(spotify.get("item").get("artists"))):
            spotify["item"]["artists"][i]["id"] = (
                (":" + (spotify.get("item").get("artists")[i].get("name"))).zfill(22))[:22]
    add_artists(spotify, cursor)
    add_song(spotify, cursor, 0)
    add_playlist_songs(cursor, spotify,  playlist, status)
    db.commit()
    db.close
    return 1

