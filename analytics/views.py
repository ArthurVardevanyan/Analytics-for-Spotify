from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.db import connection
import json


def dictfetchall(cursor):
    # https://stackoverflow.com/a/58969129
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    js = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return json.dumps(js)


def listeningHistory(request):
    query = "SELECT timePlayed, songs.name, songs.trackLength FROM `listeningHistory` INNER JOIN songs ON songs.id =listeningHistory.songID  ORDER BY timePlayed"
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json_data, content_type="application/json")


def songs(request):
    query = "SELECT songs.name as 'name', `playCount`, GROUP_CONCAT(artists.name  SEPARATOR', ') as 'artists' FROM songArtists \
    INNER JOIN songs ON songs.id=songArtists.songID \
    INNER JOIN artists ON artists.id=songArtists.artistID \
    GROUP BY songs.id"
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json_data, content_type="application/json")


def playlistSongs(request):
    query = 'SELECT playlists.lastUpdated, playlistSongs.songStatus, songs.name as "name", `playCount`, GROUP_CONCAT(artists.name  SEPARATOR", ") \
    as "artists" FROM playlistSongs\
    INNER JOIN songs ON songs.id =playlistSongs.songID \
    INNER JOIN songArtists ON songs.id=songArtists.songID \
    INNER JOIN artists ON artists.id=songArtists.artistID \
    INNER JOIN playlists ON playlists.id=playlistSongs.playlistID \
    GROUP BY songs.id  '
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json_data, content_type="application/json")
