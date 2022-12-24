import logging
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import os
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
import json
import requests
import monitoringBackend.database as database
import monitoringBackend.spotify as spotify
import webBackend.credentials as credentials
import webBackend.models as models
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

log = logging.getLogger(__name__)


def redirect(request: requests.request):
    """

    Parameters:
        request:    (request): Unused Request Object
    Returns:
        HttpResponseRedirect: HTTP Response Redirect
    """
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def health(request: requests.request):
    """

    Parameters:
        request:    (request): Unused Request Object
    Returns:
        HttpResponse: HTTP response
    """
    try:
        if connection.ensure_connection():
            return HttpResponse(status=503)
        else:
            return HttpResponse(status=200)
    except:
        log.exception("DB Error")
        return HttpResponse(status=500)


@require_GET
@ensure_csrf_cookie
def authenticated(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    if request.session.get('spotify', False) and request.method == "GET":
        response = request.session.get('spotify')
        return HttpResponse(True)
    else:
        return HttpResponse(False, status=401)


def login(request: requests.request):
    """

    Parameters:
        request:    (request): Unused Request Object
    Returns:
        HttpResponse: HTTP response
    """
    url = ""
    if(isinstance(credentials.getAPI(), dict)):
        url = '<meta http-equiv="Refresh" content="0; url=' + \
            credentials.getAPI().get("url")+'" />'
    else:
        log.warning("API Error")
        url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def loginResponse(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    url = ""
    CODE = request.GET.get("code")
    if CODE:
        credentials.setSession(request, CODE)
        url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    else:
        log.warning("Login Code Failure: " + str(request.GET))
        url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def logout(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    if(request.session.get('spotify', False) != False):
        request.session.pop('spotify')
    url = '<meta http-equiv="Refresh" content="0; url=/spotify/index.html" />'
    return HttpResponse(url, content_type="text/html")


def status(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    status = 0
    with connection.cursor() as cursor:
        query = "SELECT * from users where user = '" + \
            request.session.get('spotify') + "'"
        cursor.execute(query)
        for stat in cursor:
            status = str(stat[1])+":"+str(stat[2])+":"+str(stat[5])
    return HttpResponse(status)


def start(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
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


def stop(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET enabled = 0 where user ='" + spotifyID + "'")

    url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
    return HttpResponse(url, content_type="text/html")


def deleteUser(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    models.ListeningHistory.objects.filter(user=spotifyID).delete()
    models.PlayCount.objects.filter(user=spotifyID).delete()
    models.PlaylistsUsers.objects.filter(user=spotifyID).delete()
    models.Users.objects.filter(user=spotifyID).delete()
    url = '<meta http-equiv="Refresh" content="0; url=/spotify"/>'
    return HttpResponse(url, content_type="text/html")


def dictFetchAll(cursor: connection.cursor):
    """

    Parameters:
        cursor:    (cursor): DB Query Output Connection
    Returns:
        dict: Song Objects
    """
    # https://stackoverflow.com/a/58969129
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def listeningHistory(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    query = "SELECT timePlayed, songs.name, songs.trackLength FROM `listeningHistory` LEFT JOIN songs ON songs.id =listeningHistory.songID  \
    WHERE listeningHistory.user = '"+spotifyID + "' ORDER BY listeningHistory.id"
    cursor = connection.cursor()
    cursor.execute(query)
    return HttpResponse(json.dumps(dictFetchAll(cursor)), content_type="application/json")


def songs(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    query = "SELECT songs.name as 'name', playCount.playCount, GROUP_CONCAT(artists.name  SEPARATOR', ') as 'artists' FROM songArtists \
    INNER JOIN songs ON songs.id=songArtists.songID \
    INNER JOIN artists ON artists.id = songArtists.artistID \
    INNER JOIN playCount ON playCount.songID = songs.id WHERE playCount.user = '"+spotifyID + "'\
    GROUP BY songs.id, songs.name, playCount.playCount"
    cursor = connection.cursor()
    cursor.execute(query)
    json_data = dictFetchAll(cursor)
    return HttpResponse(json.dumps(json_data), content_type="application/json")


def playlistSubmission(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    response = ""
    try:
        playlist = request.POST.get("playlist")
        playlist = playlist.split("playlist/")[1].split("?")[0]
        url = 'https://api.spotify.com/v1/playlists/' + playlist + "?market=US"
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


def deletePlaylist(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
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


def playlistSongs(request: requests.request):
    """

    Parameters:
        request:    (request): Request Object
    Returns:
        HttpResponse: HTTP response
    """
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)
    playlistsData = []
    playlists = database.get_playlists(spotifyID)
    for playlist in playlists:
        playlistDict = {}
        query = 'SELECT playlistSongs.songStatus, songs.name as "name", playCount.playCount,\
        DATE_FORMAT(played1.timePlayed, "%Y-%m-%d") as timePlayed,\
        GROUP_CONCAT(artists.name  SEPARATOR", ") as "artists"\
        FROM playlistSongs\
        INNER JOIN songs ON songs.id =playlistSongs.songID\
        INNER JOIN songArtists ON songs.id=songArtists.songID\
        INNER JOIN artists ON artists.id=songArtists.artistID\
        INNER JOIN playlists ON playlists.playlistID=playlistSongs.playlistID\
        INNER JOIN playCount ON playCount.songID = songs.id\
        RIGHT JOIN (\
            SELECT lastPlayed_id.songId, listeningHistory.timePlayed\
            FROM `listeningHistory`\
                RIGHT JOIN (\
                    SELECT distinct songID,  max(id) as "id" FROM `listeningHistory` GROUP BY songID) \
                    AS lastPlayed_id\
                    ON lastPlayed_id.id =listeningHistory.id  )\
                    AS played1 ON played1.songID = songs.id\
        WHERE playCount.user  = "'+spotifyID + '"\
        and playlists.playlistID =  "'+playlist[0] + '"\
        GROUP BY songs.id, playlistSongs.songStatus, spotify.songs.name,spotify.playCount.playCount\
        ORDER BY `timePlayed`  ASC'
        cursor = connection.cursor()
        cursor.execute(query)
        json_data = dictFetchAll(cursor)
        playlistDict["id"] = playlist[0]
        playlistDict["name"] = playlist[1]
        playlistDict["lastUpdated"] = playlist[2]
        playlistDict["tracks"] = json_data
        playlistsData.append(playlistDict)
    return HttpResponse(json.dumps(playlistsData), content_type="application/json")
