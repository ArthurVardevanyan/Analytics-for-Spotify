import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
import json
import requests
import time
import hashlib
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
key = []
try:
    with open("credentials/spotifyCredentials.txt") as f:
        key = f.readlines()
    key = [x.strip() for x in key]
except Exception as e:
    print(e)
    print("Credential Failure")


def authenticated(request):
    if request.session.get('spotify'):
        response = request.session.get('spotify')
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def logout(request):
    request.session.pop('spotify')
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def dictfetchall(cursor):
    # https://stackoverflow.com/a/58969129
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    js = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return json.dumps(js)


def listeningHistory(request):
    spotifyID = request.session.get('spotify')
    query = "SELECT timePlayed, songs.name, songs.trackLength FROM `listeningHistory` INNER JOIN songs ON songs.id =listeningHistory.songID  \
    WHERE listeningHistory.user = '"+spotifyID + "' \
    ORDER BY timePlayed"
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json_data, content_type="application/json")


def songs(request):
    spotifyID = request.session.get('spotify')
    query = "SELECT songs.name as 'name', playcount.playCount, GROUP_CONCAT(artists.name  SEPARATOR', ') as 'artists' FROM songArtists \
    INNER JOIN songs ON songs.id=songArtists.songID \
    INNER JOIN artists ON artists.id = songArtists.artistID \
	INNER JOIN playcount ON playcount.songID = songs.id WHERE playcount.user = '"+spotifyID + "'\
    GROUP BY songs.id"
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json_data, content_type="application/json")


def playlistSongs(request):
    spotifyID = request.session.get('spotify')
    query = 'SELECT playlists.lastUpdated, playlistSongs.songStatus, songs.name as "name", playcount.playCount, GROUP_CONCAT(artists.name  SEPARATOR", ") \
    as "artists" FROM playlistSongs\
    INNER JOIN songs ON songs.id =playlistSongs.songID \
    INNER JOIN songArtists ON songs.id=songArtists.songID \
    INNER JOIN artists ON artists.id=songArtists.artistID \
    INNER JOIN playlists ON playlists.id=playlistSongs.playlistID \
    INNER JOIN playcount ON playcount.songID = songs.id WHERE playcount.user  = "'+spotifyID + '" and playlists.user =  "'+spotifyID + '"\
    GROUP BY songs.id'
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictfetchall(cursor)
    return HttpResponse(json_data, content_type="application/json")


def userHash(auth):
    url = "https://api.spotify.com/v1/me"
    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + auth.get("access_token")}
    result = hashlib.sha512(str.encode(
        requests.get(url, headers=header).json().get("id")))
    return result.hexdigest()


def accessToken(request, CODE):
    CS = key[4]
    URI = "http://localhost/analytics/loginResponce"
    url = 'https://accounts.spotify.com/api/token'
    # "Accept": "application/json",
    # "Content-Type": "application/json",
    header = {"Authorization": "Basic " + CS}
    data = {
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": URI}
    response = requests.post(url, headers=header, data=data)
    auth = response.json()
    currentTime = int(time.time())
    expire = auth.get("expires_in")
    auth["expires_at"] = currentTime + expire
    userID = userHash(auth)
    request.session['spotify'] = userID  # SESSION
    with open('.cache-' + userID, 'w+') as f:
        json.dump(auth, f, indent=4, separators=(',', ': '))

    query = "INSERT IGNORE INTO users (`user`, `enabled`, `statusSong`, `statusPlaylist`) VALUES ('" + \
        userID + "', 0, 0, 0) "
    cursor = connection.cursor()
    cursor.execute(query)

    return response


def login(request):
    url = '<meta http-equiv="Refresh" content="0; url='+key[3]+'" />'
    return HttpResponse(url, content_type="text/html")


def loginResponce(request):
    # http://localhost:8000/analytics/loginResponce
    CODE = request.GET.get("code")
    accessToken(request, CODE)
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/spotify.html" />'
    return HttpResponse(url, content_type="text/html")


def status(request):
    spotifyID = request.session.get('spotify')
    status = 0
    with connection.cursor() as cursor:
        query = "SELECT * from users where user = '" + \
            request.session.get('spotify') + "'"
        cursor.execute(query)
        for stat in cursor:
            status = stat[1]
    return HttpResponse(status)


def stop(request):
    spotifyID = request.session.get('spotify')
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET enabled = 0 where user ='" + spotifyID + "'")

    url = '<meta http-equiv="Refresh" content="0; url=/spotify/spotify.html" />'
    return HttpResponse(url, content_type="text/html")


def start(request):
    spotifyID = request.session.get('spotify')
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET enabled = 1 where user ='" + spotifyID + "'")

    url = '<meta http-equiv="Refresh" content="0; url=/spotify/spotify.html" />'
    return HttpResponse(url, content_type="text/html")
