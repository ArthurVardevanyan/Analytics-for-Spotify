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

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
key = []
API = ""
# try:
#     with open("credentials/spotifyCredentials.txt") as f:
#         key = f.readlines()
#     key = [x.strip() for x in key]
# except Exception as e:
#     print(e)
#     print("Credential Failure")
f = ""


def encryptJson(auth):
    # thepythoncode.com/article/encrypt-decrypt-files-symmetric-python
    # initialize the Fernet class
    # encrypt the message
    return (f.encrypt(str(auth).encode())).decode("utf-8")


def decryptUserJson(userID):
    userData = ""
    with connection.cursor() as cursor:
        users = "SELECT * from users  WHERE user = '" + userID + "'"
        cursor.execute(users)
        for user in cursor:
            userData = user
    # thepythoncode.com/article/encrypt-decrypt-files-symmetric-python
    # initialize the Fernet class
    # encrypt the message
    return ast.literal_eval((f.decrypt(userData[4]).decode("utf-8")))


def apiDecrypt():
    with connection.cursor() as cursor:
        api = "SELECT * from spotifyAPI"
        cursor.execute(api)
        for api in cursor:
            return ast.literal_eval((f.decrypt(api[0]).decode("utf-8")))


@csrf_exempt
def boot(request):
    t = (request.POST.get("code")).encode()
    try:
        global f
        f = Fernet(t)
        global API
        API = apiDecrypt()
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
    header = {"Authorization": "Basic " + API.get("B64CS")}
    data = {
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": "http://localhost/analytics/loginResponce"}
    response = requests.post(
        'https://accounts.spotify.com/api/token', headers=header, data=data)
    auth = response.json()
    currentTime = int(time.time())
    expire = auth.get("expires_in")
    auth["expires_at"] = currentTime + expire
    userID = userHash(auth)
    request.session['spotify'] = userID  # SESSION
    # with open('.cache-' + userID, 'w+') as f:
    #    json.dump(auth, f, indent=4, separators=(',', ': '))
    cache = encryptJson(auth)
    query = "INSERT IGNORE INTO users (`user`, `enabled`, `statusSong`, `statusPlaylist`, `cache`) VALUES ('" + \
        userID + "', 0, 0, 0, '"+cache+"') "
    cursor = connection.cursor()
    cursor.execute(query)
    query = "UPDATE users SET cache = '"+cache+"' WHERE user = '" + userID + "'"
    cursor.execute(query)
    return response


def login(request):
    url = '<meta http-equiv="Refresh" content="0; url='+API.get("url")+'" />'
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
            status = str(stat[1])+":"+str(stat[2])
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
        user = database.user_status(spotifyID, 1)
        if(user[2] == 0):
            spotify.SpotifyThread(user)
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/spotify.html" />'
    return HttpResponse(url, content_type="text/html")


def refresh_token(userID):
    # Checks For and Provides Refresh Token
    access = ''
    # with open('.cache-' + userID) as json_file:
    #    access = json.load(json_file)
    access = decryptUserJson(userID)
    if(int(time.time()) >= access["expires_at"]):
        header = {"Authorization": "Basic " + API.get("B64CS")}
        data = {"grant_type": "refresh_token",
                "refresh_token": access.get("refresh_token"),
                "redirect_uri": "http://localhost/analytics/loginResponce"}
        response = requests.post(
            'https://accounts.spotify.com/api/token', headers=header, data=data)
        auth = response.json()
        currentTime = int(time.time())
        expire = auth.get("expires_in")
        auth["expires_at"] = currentTime + expire
        auth["refresh_token"] = auth.get(
            "refresh_token", access.get("refresh_token"))
        # with open('.cache-' + userID, 'w+') as f:
        #    json.dump(auth, f, indent=4, separators=(',', ': '))
        cache = encryptJson(auth)
        cursor = connection.cursor()
        query = "UPDATE users SET cache = '"+cache+"' WHERE user = '" + userID + "'"
        cursor.execute(query)
        return auth.get("access_token")
    else:
        return access.get("access_token")
