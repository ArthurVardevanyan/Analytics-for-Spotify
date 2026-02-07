import logging
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import os
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.db.models import F
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
            return HttpResponse(spotify.WORKER, status=503)
        else:
            if spotify.WORKER_HEALTHY and spotify.WORKER != None:
                return HttpResponse(spotify.WORKER, status=200)
            else:
                return HttpResponse(spotify.WORKER, status=503)
    except:
        log.exception("DB Error")
        return HttpResponse(spotify.WORKER, status=500)

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
        success = credentials.setSession(request, CODE)
        if success:
            url = '<meta http-equiv="Refresh" content="0; url=/spotify/analytics.html" />'
        else:
            log.warning("Authentication Failed - User may not be whitelisted in Spotify Developer App")
            url = '<div style="font-family: Arial; padding: 20px;"><h2>Authentication Failed</h2><p>Your Spotify account is not authorized to use this application.</p><p>If this app is in Development Mode, please contact the administrator to add your account to the allowlist.</p><a href="/spotify/index.html">Return to Home</a></div>'
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

    # Support optional limit parameter for lazy loading
    limit = request.GET.get('limit', None)

    query = models.ListeningHistory.objects.filter(
        user=str(spotifyID)).select_related(
        "songID").values(t=F("timePlayed"),n=F("songID__name")).order_by('-t')

    if limit:
        try:
            query = query[:int(limit)]
        except ValueError:
            pass  # Invalid limit, return all

    return JsonResponse(list(query), safe=False)


def stats(request: requests.request):
    """
    Calculate listening stats

    Parameters:
        request:    (request): Request Object
    Returns:
        JsonResponse: JSON with songs count and hours listened
    """
    from django.db.models import Sum, Count
    import time
    from django.db import connection

    start = time.time()
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)

    # Use database aggregation instead of Python loop
    result = models.ListeningHistory.objects.filter(
        user=str(spotifyID)
    ).aggregate(
        total_songs=Count('id'),
        total_time=Sum('songID__trackLength')
    )

    songsListenedTo = result['total_songs'] or 0
    timeListened = round((result['total_time'] or 0) / 60000 / 60 * 10) / 10

    log.debug(f"Stats - Total time: {time.time() - start:.3f}s, Queries: {len(connection.queries)}")

    return JsonResponse({
        "songsListenedTo": songsListenedTo,
        "hoursListened": timeListened
    })

def dailyAggregation(request: requests.request):
    """
    Get daily listening aggregation

    Parameters:
        request:    (request): Request Object
    Returns:
        JsonResponse: JSON with daily song counts
    """
    from django.db.models import Count
    from django.db.models.functions import Substr
    import time
    from django.db import connection

    start = time.time()
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)

    # Extract date from timePlayed text field (format: "YYYY-MM-DD HH:MM:SS")
    # For timezone conversion, we need to use raw SQL since timePlayed is text
    from django.db.models import CharField
    from django.db.models.functions import Cast
    from datetime import datetime

    # Use raw SQL for timezone conversion from UTC to local time
    daily_data = models.ListeningHistory.objects.filter(
        user=str(spotifyID)
    ).extra(
        select={
            'local_date': 'DATE(("timePlayed" || \'+00\')::timestamptz AT TIME ZONE \'America/Detroit\')'
        }
    ).values('local_date').annotate(
        count=Count('id')
    ).order_by('local_date')

    # Convert to the format expected by frontend
    songs = []
    plays = []
    for item in daily_data:
        songs.append(str(item['local_date']))
        plays.append(item['count'])

    log.debug(f"DailyAgg - Total time: {time.time() - start:.3f}s, Days: {len(songs)}, Queries: {len(connection.queries)}")

    return JsonResponse({
        "songs": songs,
        "plays": plays
    })

def hourlyAggregation(request: requests.request):
    """
    Get hourly listening aggregation

    Parameters:
        request:    (request): Request Object
    Returns:
        JsonResponse: JSON with hourly song counts
    """
    from django.db.models import Count
    import time
    from django.db import connection

    start = time.time()
    spotifyID = request.session.get('spotify', False)
    if(spotifyID == False):
        return HttpResponse(status=401)

    # Use database-level hour extraction with proper timezone conversion
    # timePlayed is stored as text in format "YYYY-MM-DD HH:MM:SS" in UTC
    hourly_data = models.ListeningHistory.objects.filter(
        user=str(spotifyID)
    ).extra(
        select={'local_hour': 'EXTRACT(HOUR FROM ("timePlayed" || \'+00\')::timestamptz AT TIME ZONE \'America/Detroit\')'}
    ).values('local_hour').annotate(
        count=Count('id')
    ).order_by('local_hour')

    # Initialize all hours to 0
    hourly_counts = [0] * 24
    for item in hourly_data:
        hour = int(item['local_hour'])
        hourly_counts[hour] = item['count']

    songs = [f"{i:02d}" for i in range(24)]
    plays = hourly_counts

    log.debug(f"HourlyAgg - Total time: {time.time() - start:.3f}s, Queries: {len(connection.queries)}")

    return JsonResponse({
        "songs": songs,
        "plays": plays
    })

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

    userObject = models.Users.objects.get(
        user=str(spotifyID))

    # Get Song Play Count without Artists
    playCount = models.PlayCount.objects.filter(user=userObject).select_related().values(
        'songID', 'songID__name', 'playCount', )

    # Get SongID, Artist Name Combo
    playCountArtist = models.PlayCount.objects.filter(user=userObject).select_related().values(
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
                "n": song['songID__name'],
                "pc": song['playCount'],
                "a": playCountArtistDict.get(song["songID"], "")
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
    if(status.statusPlaylist > 0):
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

    # Get List of Playlists Belonging to User
    playlists = database.get_playlists(spotifyID)

    # Get User Object
    userObject = models.Users.objects.get(
        user=str(spotifyID))

    # Get Play Count History for User
    playCount = list(models.PlayCount.objects.filter(user=userObject).select_related().values(
        'songID', 'playCount'))
    playCountDict = {}
    for pc in playCount:
        playCountDict[pc['songID']] = pc.get('playCount', 0)

    # Get Listening History for User, and Store only Last Played
    listeningHistory = list(models.ListeningHistory.objects.filter(
        user=userObject).select_related().values(
            'songID', 'timePlayed').order_by('timePlayed'))
    listeningHistoryLatest = {}
    for lh in listeningHistory:
        listeningHistoryLatest[lh['songID']] = lh['timePlayed']

    # Get List of all Song <--> Artist Relationships
    songArtists = list(models.Songs.objects.select_related(
    ).all().values('id', 'artists__name'))

    # MYSQL GROUP_CONCAT Logic in Python
    songArtistsDict = {}
    for artist in songArtists:
        songArtistsDict[
            artist['id']] = str(artist["artists__name"]) + ", " + str(songArtistsDict.get(artist['id'], " "))

    # For Each Playlist, build data for Table
    for playlist in playlists:
        playlistDict = {}

        # Get All Songs In Playlist
        playlistSongs = list(models.PlaylistSongs.objects.select_related(
            'songID').filter(playlistID=playlist).values('songID', 'songStatus', 'songID__name'))

        playlistData = []
        for ps in playlistSongs:
            # Append All Information Gathered Previously
            playlistData.append({
                "ss": ps['songStatus'],
                "n": ps['songID__name'],
                "pc": playCountDict.get(ps['songID'], 0),
                "t": listeningHistoryLatest.get(ps['songID'], "1970-01-01").split(" ")[0],
                "a": str(songArtistsDict.get(ps['songID'], "")).rstrip(', ')
            })

        playlistDict["id"] = playlist[0]
        playlistDict["name"] = playlist[1]
        playlistDict["lastUpdated"] = playlist[2]
        playlistDict["tracks"] = sorted(
            playlistData, key=lambda x: x['t'])
        playlistsData.append(playlistDict)
    return HttpResponse(json.dumps(playlistsData), content_type="application/json")
