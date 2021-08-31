from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
import json
import requests
import time
import songMonitoringBackend.database as database
import songMonitoringBackend.spotify as spotify
import webBackend.credentials as credentials
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@csrf_exempt
def boot(request=0):

    try:
        spotify.main()
    except Exception as e:
        print(e)
        # exit()
        return HttpResponse("", content_type="text/html")
    return HttpResponse("", content_type="text/html")


def authenticated(request):
    if request.session.get('spotify'):
        response = request.session.get('spotify')
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def logout(request):
    if(request.session.get('spotify', False) != False):
        request.session.pop('spotify')
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def redirect(request):
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def dictfetchall(cursor):
    # https://stackoverflow.com/a/58969129
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def listeningHistory(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    query = "SELECT timePlayed, songs.name, songs.trackLength FROM `listeningHistory` LEFT JOIN songs ON songs.id =listeningHistory.songID  \
    WHERE listeningHistory.user = '"+spotifyID + "' ORDER BY listeningHistory.id"
    cursor = connection.cursor()
    cursor.execute(query)
    return HttpResponse(json.dumps(dictfetchall(cursor)), content_type="application/json")


def songs(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    query = "SELECT songs.name as 'name', playcount.playCount, GROUP_CONCAT(artists.name  SEPARATOR', ') as 'artists' FROM songArtists \
    INNER JOIN songs ON songs.id=songArtists.songID \
    INNER JOIN artists ON artists.id = songArtists.artistID \
	INNER JOIN playcount ON playcount.songID = songs.id WHERE playcount.user = '"+spotifyID + "'\
    GROUP BY songs.id"
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json.dumps(json_data), content_type="application/json")


def playlistSongs(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    playlistsData = []
    playlists = database.get_playlists(spotifyID)
    for playlist in playlists:
        playlistDict = {}
        query = 'SELECT playlists.lastUpdated, playlistSongs.songStatus, songs.name as "name", playcount.playCount,\
        DATE_FORMAT(played1.timePlayed, "%Y-%m-%d") as timePlayed,\
	    GROUP_CONCAT(artists.name  SEPARATOR", ") as "artists"\
        FROM playlistSongs\
        INNER JOIN songs ON songs.id =playlistSongs.songID\
        INNER JOIN songArtists ON songs.id=songArtists.songID\
        INNER JOIN artists ON artists.id=songArtists.artistID\
        INNER JOIN playlists ON playlists.playlistID=playlistSongs.playlistID\
        INNER JOIN playcount ON playcount.songID = songs.id\
        LEFT JOIN (\
        		SELECT `songID`, `timePlayed`\
            	FROM(\
                    SELECT `songID`, `timePlayed`,\
      					  (ROW_NUMBER() OVER (PARTITION BY songID ORDER BY timePlayed DESC)) as rn\
       				FROM `listeningHistory`  )\
            		AS played0 WHERE `rn` = 1)\
                    AS played1 ON played1.songID = songs.id\
        WHERE playcount.user  = "'+spotifyID + '"\
        and playlists.playlistID =  "'+playlist[0] + '"\
        GROUP BY songs.id'
        cursor = connection.cursor()
        cursor.execute(query)
        json_data = dictfetchall(cursor)
        playlistDict["id"] = playlist[0]
        playlistDict["name"] = playlist[1]
        playlistDict["tracks"] = json_data
        playlistsData.append(playlistDict)
    return HttpResponse(json.dumps(playlistsData), content_type="application/json")


def login(request):
    url = ""
    if(isinstance(credentials.getAPI(), dict)):
        url = '<meta http-equiv="Refresh" content="0; url=' + \
            credentials.getAPI().get("url")+'" />'
    else:
        url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def loginResponse(request):
    CODE = request.GET.get("code")
    credentials.accessToken(request, CODE)
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")


def status(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    status = 0
    with connection.cursor() as cursor:
        query = "SELECT * from users where user = '" + \
            request.session.get('spotify') + "'"
        cursor.execute(query)
        for stat in cursor:
            status = str(stat[1])+":"+str(stat[2])
    return HttpResponse(status)


def stop(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET enabled = 0 where user ='" + spotifyID + "'")

    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")


def deleteUser(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    cursor = connection.cursor()
    query = "DELETE FROM `users`  WHERE user = '" + spotifyID + "'"
    cursor.execute(query)
    url = '<meta http-equiv="Refresh" content="0; url=/spotify"/>'
    return HttpResponse(url, content_type="text/html")


def start(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET enabled = 1 where user ='" + spotifyID + "'")
        user = database.user_status(spotifyID, 1)
        if(user[2] == 0):
            spotify.SpotifyThread(user)
            spotify.songIdUpdaterThread(user)
        if(user[3] == 0):
            spotify.playlistSongThread(spotifyID[0])

    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")


def playlistSubmission(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    response = ""
    try:
        playlist = request.POST.get("playlist")
        playlist = playlist.split("playlist/")[1].split("?")[0]
        url = 'https://api.spotify.com/v1/playlists/' + \
            playlist + "?market=US"
        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + credentials.refresh_token(spotifyID)}
        response = requests.get(url, headers=header).json()
        if (not response.get("href", False)):
            return HttpResponse(status=400)
    except:
        return HttpResponse(status=401)

    add = ("INSERT IGNORE INTO playlists"
           "(playlistID, name, lastUpdated)"
           "VALUES (%s, %s, %s)")
    data = (
        playlist,
        response.get('name'),
        "N/A",
    )
    cursor = connection.cursor()
    cursor.execute(add, data)
    add = ("INSERT IGNORE INTO playlistsUsers"
           "(user, playlistID)"
           "VALUES (%s, %s)")
    data = (
        spotifyID,
        playlist,
    )
    cursor.execute(add, data)
    status = database.user_status(spotifyID, 1)
    if(status[3] > 0):
        spotify.playlistSongThread(spotifyID, 1)
    else:
        spotify.playlistSongThread(spotifyID)
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")


def deletePlaylist(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    playlist = request.POST.get("playlist")
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM `playlistSongs` WHERE playlistID = %s",  (playlist, ))
    cursor.execute(
        "DELETE FROM `playlistsUsers` WHERE user = %s and  playlistID = %s", (spotifyID, playlist, ))
    cursor.execute(
        "SELECT * from playlistsUsers WHERE playlistID = %s",  (playlist, ))
    playlists = 0
    for p in cursor:
        playlist += 1
    if playlists == 0:
        cursor.execute(
            "DELETE FROM `playlists` WHERE playlistID = %s",  (playlist, ))
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")
