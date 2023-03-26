import logging
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import os
from django.http import HttpResponse, JsonResponse

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

    user = models.Users.objects.get(user=str(request.session.get('spotify')))
    status = str(user.enabled)+":"+str(user.statusSong) + \
        ":"+str(user.realtime)

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
    models.Users.objects.filter(
        user=str(spotifyID)).update(enabled=1)
    user = database.user_status(spotifyID, 1)

    if(user.statusSong == 0):
        spotify.SpotifyThread(user)
        spotify.songIdUpdaterThread(user.user)
    if(user.statusPlaylist == 0):
        spotify.playlistSongThread(spotifyID)

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

    models.Users.objects.filter(
        user=str(spotifyID)).update(enabled=0)

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

    listeningHistory = models.ListeningHistory.objects.filter(
        user=str(spotifyID)).select_related(
        "songID").values('timePlayed', 'songID__name', 'songID__trackLength')

    return JsonResponse(list(listeningHistory), safe=False)


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

    # Get Song Play Count without Artists
    playCount = models.PlayCount.objects.select_related().values(
        'songID', 'songID__name', 'playCount', )

    # Get SongID, Artist Name Combo
    playCountArtist = models.PlayCount.objects.select_related().values(
        'songID', 'songID__artists__name')

    # Group Concat Artist with Comma onto SongIDs
    playCountArtistDict = {}
    playCountArtistList = list(playCountArtist)
    for artist in playCountArtistList:
        try:
            playCountArtistDict[artist["songID"]] = str(
                playCountArtistDict[artist["songID"]]) + ", " + str(artist["songID__artists__name"])
        except:
            playCountArtistDict[artist["songID"]
                                ] = artist["songID__artists__name"]

    # Add Comma Separated Artists to Song Play Count
    playCountGroupConcat = []
    for song in list(playCount):
        playCountGroupConcat.append(
            {
                "songID__name": song['songID__name'],
                "playCount": song['playCount'],
                "songID__artists__name": playCountArtistDict[song["songID"]]
            }
        )

    return JsonResponse(playCountGroupConcat, safe=False)


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

    playlists = models.Playlists.objects.filter(
        playlistID=playlist).count()
    if playlists == 0:
        models.Playlists.objects.create(
            playlistID=playlist, name=response.get('name'), lastUpdated="N/A",)

    playlistUsers = models.PlaylistsUsers.objects.filter(
        playlistID=playlist).count()
    if playlistUsers == 0:
        models.PlaylistsUsers.objects.create(
            playlistID=models.Playlists.objects.get(playlistID=str(playlist)),
            user=models.Users.objects.get(user=str(spotifyID)))

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
    models.PlaylistSongs.objects.filter(playlistID=playlist).delete()
    models.PlaylistsUsers.objects.filter(
        user=spotifyID, playlistID=playlist).delete()
    playlists = models.PlaylistsUsers.objects.filter(
        playlistID=playlist).count()
    if playlists == 0:
        models.Playlists.objects.filter(playlistID=playlist).delete()
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
        query = """SELECT playlistSongs.songStatus, songs.name as "name", playCount.playCount,
        DATE_FORMAT(played1.timePlayed, "%%Y-%%m-%%d") as timePlayed,
        GROUP_CONCAT(artists.name  SEPARATOR", ") as "artists"
        FROM playlistSongs
        INNER JOIN songs ON songs.id =playlistSongs.songID
        INNER JOIN songs_artists ON songs.id=songs_artists.songs_id
        INNER JOIN artists ON artists.id=songs_artists.artists_id
        INNER JOIN playlists ON playlists.playlistID=playlistSongs.playlistID
        INNER JOIN playCount ON playCount.songID = songs.id
        RIGHT JOIN (
            SELECT lastPlayed_id.songId, listeningHistory.timePlayed
            FROM `listeningHistory`
                RIGHT JOIN (
                    SELECT distinct songID,  max(id) as "id" FROM `listeningHistory` GROUP BY songID)
                    AS lastPlayed_id
                    ON lastPlayed_id.id =listeningHistory.id  )
                    AS played1 ON played1.songID = songs.id\
        WHERE playCount.user  =  %s
        and playlists.playlistID = %s
        GROUP BY songs.id, playlistSongs.songStatus, spotify.songs.name,spotify.playCount.playCount
        ORDER BY `timePlayed`  ASC"""
        cursor = connection.cursor()
        cursor.execute(query, (str(spotifyID),  str(playlist[0])))
        json_data = dictFetchAll(cursor)
        playlistDict["id"] = playlist[0]
        playlistDict["name"] = playlist[1]
        playlistDict["lastUpdated"] = playlist[2]
        playlistDict["tracks"] = json_data
        playlistsData.append(playlistDict)
    return HttpResponse(json.dumps(playlistsData), content_type="application/json")
