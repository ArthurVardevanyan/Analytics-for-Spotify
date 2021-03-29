from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
import json
import requests
import time
import database
import spotify
import hashlib
import cryptography
from cryptography.fernet import Fernet
import ast
import analytics.credentials as cred
from SpotifyAnalytics.env import ENCRYPTION, PRIVATE

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@csrf_exempt
def boot(request=0):
    t = 0
    if(ENCRYPTION == 0):
        spotify.main()
        cred.API = cred.apiDecrypt()
        return HttpResponse("", content_type="text/html")
    if(ENCRYPTION == 1):
        t = PRIVATE
    if(ENCRYPTION == 2):
        t = (request.POST.get("code")).encode()
    try:
        cred.f = Fernet(t)
        cred.API = cred.apiDecrypt()
        spotify.main()
    except Exception as e:
        e = e
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


def dictfetchall(cursor):
    # https://stackoverflow.com/a/58969129
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def listeningHistory(request):
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    query = "SELECT timePlayed, songs.name, songs.trackLength FROM `listeningHistory` INNER JOIN songs ON songs.id =listeningHistory.songID  \
    WHERE listeningHistory.user = '"+spotifyID + "' \
    ORDER BY timePlayed"
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
        query = 'SELECT playlists.lastUpdated, playlistSongs.songStatus, songs.name as "name", playcount.playCount, GROUP_CONCAT(artists.name  SEPARATOR", ") \
        as "artists" FROM playlistSongs\
        INNER JOIN songs ON songs.id =playlistSongs.songID \
        INNER JOIN songArtists ON songs.id=songArtists.songID \
        INNER JOIN artists ON artists.id=songArtists.artistID \
        INNER JOIN playlists ON playlists.id=playlistSongs.playlistID \
        INNER JOIN playcount ON playcount.songID = songs.id WHERE playcount.user  = "'+spotifyID + '" and playlists.user =  "'+spotifyID + '"\
        and playlists.id =  "'+playlist[0] + '"\
        GROUP BY songs.id'
        cursor = connection.cursor()
        cursor.execute(query)
        json_data = dictfetchall(cursor)
        playlistDict["name"] = playlist[2]
        playlistDict["hash"] = playlist[0]
        playlistDict["tracks"] = json_data
        playlistsData.append(playlistDict)
    return HttpResponse(json.dumps(playlistsData), content_type="application/json")


def userHash(auth):
    url = "https://api.spotify.com/v1/me"
    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + auth.get("access_token")}
    result = requests.get(url,
                          headers=header).json().get("id")
    if(ENCRYPTION):
        result = hashlib.sha512(str.encode(cred.API.get("salt") + result))
        return result.hexdigest()
    else:
        return result


def accessToken(request, CODE):
    header = {"Authorization": "Basic " + cred.API.get("B64CS")}
    data = {
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": cred.API.get("redirect_url")}
    response = requests.post(
        'https://accounts.spotify.com/api/token', headers=header, data=data)
    auth = response.json()
    currentTime = int(time.time())
    expire = auth.get("expires_in")
    auth["expires_at"] = currentTime + expire
    userID = ""
    userID = userHash(auth)
    request.session['spotify'] = userID  # SESSION
    cache = cred.encryptContent(auth)
    query = 'INSERT IGNORE INTO users (`user`, `enabled`, `statusSong`, `statusPlaylist`, `cache`) VALUES ("' + \
        userID + '", 0, 0, 0, "'+cache+'") '
    cursor = connection.cursor()
    cursor.execute(query)
    query = 'UPDATE users SET cache = "'+cache+'" WHERE user = "' + userID + '"'
    cursor.execute(query)
    return True


def login(request):
    url = ""
    if(isinstance(cred.API, dict)):
        url = '<meta http-equiv="Refresh" content="0; url=' + \
            cred.API.get("url")+'" />'
    else:
        url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def loginResponse(request):
    CODE = request.GET.get("code")
    accessToken(request, CODE)
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
        if(user[3] == 0):
            spotify.playlistSongThread(spotifyID[0])

    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")


def playlistSubmission(request):
    from analytics.credentials import refresh_token as authorize
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    response = ""
    try:
        playlist = request.GET.get("playlist")
        playlist = playlist.split("playlist/")[1].split("?")[0]
        url = 'https://api.spotify.com/v1/playlists/' + \
            playlist + "?market=US"
        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + authorize(spotifyID)}
        response = requests.get(url, headers=header).json()
        if (not response.get("href", False)):
            return HttpResponse(status=400)
    except:
        return HttpResponse(status=401)
    if(ENCRYPTION):
        playlistHash = hashlib.sha512(str.encode(
            cred.API.get("salt") + playlist)).hexdigest()
    else:
        playlistHash = playlist
    playlistEncrypt = cred.encryptContent(playlist)

    add = ("INSERT IGNORE INTO playlists"
           "(user, id,name, lastUpdated,idEncrypt)"
           "VALUES (%s, %s, %s, %s, %s)")
    data = (
        spotifyID,
        playlistHash,
        cred.encryptContent(response.get('name')),
        "N/A",
        playlistEncrypt,
    )
    cursor = connection.cursor()
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
    playlist = request.GET.get("playlist")
    cursor = connection.cursor()
    query = "DELETE FROM `playlists`  WHERE user = '" + \
        spotifyID + "' and  id = '" + playlist + "'"
    cursor.execute(query)
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")
