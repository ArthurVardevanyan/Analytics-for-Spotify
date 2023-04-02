from datetime import datetime
import sys
from random import randint
import logging
import sys
import webBackend.models as models
sys.path.append("..")

log = logging.getLogger(__name__)


def scanWorkers(workerID: int):
    """
    Boots the Spotify Monitoring Backend.
    Assigns this Instance an UID into the Database

    Parameters:
        int: Current Worker ID
    Returns:
        int: Worker Count
    """
    utc_time = datetime.now()
    currentEpoch = int(utc_time.astimezone().timestamp())
    models.Workers.objects.filter(worker=str(workerID)).update(
        lastUpdated=str(currentEpoch), updatedTime=str(utc_time.strftime("%Y-%m-%d %H:%M:%S")))
    count = 0
    for worker in models.Workers.objects.all():
        if currentEpoch - worker.lastUpdated > 90:
            models.Workers.objects.filter(
                worker=str(worker.worker)).delete()
        else:
            count += 1
    return count


def createWorker():
    """
    Boots the Spotify Monitoring Backend.
    Assigns this Instance an UID into the Database

    Parameters:
        None
    Returns:
        int: Current Worker ID
    """
    workerID = randint(10**(9-1), (10**9)-1)
    utc_time = datetime.now()
    currentEpoch = int(utc_time.astimezone().timestamp())
    currentTime = utc_time.strftime("%Y-%m-%d %H:%M:%S")

    models.Workers(worker=workerID, lastUpdated=currentEpoch,
                   creationTime=currentTime, updatedTime=currentTime).save()

    return workerID


def user_status(user: str, detailed: int = 0):
    """
    Return Status of User

    Parameters:
        user        (str)  : User ID
        detailed    (int)  : Whether to Return Detailed output or not.
    Returns:
        models.Users | str: Depends on if Detailed Output or not.
    """

    users = models.Users.objects.filter(user=str(user))
    if(detailed):
        return users.first()
    else:
        return users.first().enabled


def add_artists(spotify: dict):
    """
    Add Artist to Artist List

    Parameters:
        spotify     (dict)  : Dictionary Containing Song Details
    Returns:
        int: unused return
    """
    for iter in spotify.get("item").get("artists"):
        count = models.Artists.objects.filter(id=iter.get("id")).count()
        if count == 0:
            models.Artists.objects.create(
                id=iter.get("id"), name=iter.get("name"))
        else:
            models.Artists.objects.filter(id=iter.get(
                "id")).update(name=iter.get("name"))
    return 0


def add_song_artists(spotify: dict, song: models.Songs):
    """
    Add Song / Artist to Song / Artist List

    Parameters:
        spotify     (dict)  : Dictionary Containing Song Details
    Returns:
        int: unused return
    """
    for iter in spotify.get("item").get("artists"):
        song.artists.add(models.Artists.objects.get(
            id=str(iter.get("id"))))
    return 0


def add_song_count(user: str, spotify: dict, count: int = 1):
    """
    Add Song / Artist to Song / Artist List

    Parameters:
        user        (str)   : User ID
        spotify     (dict)  : Dictionary Containing Song Details
        count       (int)   : PlayCount is set to 0 when inputting unplayed songs from playlist.
    Returns:
        int: unused return
    """
    song = str(spotify.get("item").get("id"))
    songID = models.Songs.objects.get(id=str(song))
    userObject = models.Users.objects.get(user=str(user))

    songPlayCount = models.PlayCount.objects.filter(
        songID=songID,
        user=userObject
    )

    playCount = -1
    if songPlayCount.count() != 0:
        playCount = int(songPlayCount.values('playCount').first()['playCount'])
    if playCount < 0:
        models.PlayCount.objects.create(
            user=userObject,
            songID=songID,
            playCount=count
        )
        add_song_artists(spotify, songID)
    else:
        playCount = playCount + count

        models.PlayCount.objects.filter(
            user=userObject,
            songID=songID,
        ).update(
            playCount=str(playCount)
        )
    return 0


def add_song(spotify: dict):
    """
    Add Song to Song List

    Parameters:
        spotify     (dict)  : Dictionary Containing Song Details
    Returns:
        int: unused return
    """

    song = None
    songID = spotify.get("item").get("id")
    count = models.Songs.objects.filter(id=songID).count()

    if count == 0:
        song = models.Songs.objects.create(
            id=songID,
            name=spotify.get("item").get("name"),
            trackLength=spotify.get("item").get("duration_ms")
        )
    else:
        models.Songs.objects.filter(
            id=songID,
        ).update(
            name=spotify.get("item").get("name"),
            trackLength=spotify.get("item").get("duration_ms")
        )

        song = models.Songs.objects.get(id=songID)

    add_song_artists(spotify, song)

    return 0


def listening_history(user: str, spotify: dict):
    """
    Add Song to Listening History

    Parameters:
        user        (str)   : User ID
        spotify     (dict)  : Dictionary Containing Song Details
    Returns:
        bool: Whether Song is Duplicate or Not.
    """
    songID = str(spotify.get("item").get("id"),)
    utc_timestamp = int(spotify.get("utc_timestamp")),
    utc_timePlayed = str(spotify.get("utc_timePlayed")),

    # This shouldn't be needed, but the Dictionary is Returning a Tuple when it shouldn't be.
    utc_timestamp = utc_timestamp[0]
    utc_timePlayed = utc_timePlayed[0]

    listeningHistory = models.ListeningHistory.objects.get_or_create(
        user=models.Users.objects.get(user=str(user)),
        songID=models.Songs.objects.get(id=songID),
        timestamp=utc_timestamp,
        timePlayed=utc_timePlayed
    )

    if (listeningHistory[1] == False):
        logging.warning("Duplicate History Song: " + songID)
        return False
    return True


def get_playlists(user: str):
    """
    Get List of Playlists from Associated User

    Parameters:
        user        (str)   : User ID
    Returns:
        list: List of Playlists
    """

    playlistsList = models.PlaylistsUsers.objects.filter(
        user_id=user).select_related('playlistID').values('playlistID', 'playlistID__name', 'playlistID__lastUpdated')

    playlists = []
    for playlist in playlistsList:
        playlists.append(
            (playlist['playlistID'], playlist['playlistID__name'], playlist['playlistID__lastUpdated']))
    return playlists


def add_playlist(playlist: str):
    """
    Create Playlist In Database

    Parameters:
        playlist    (str)   : Which Playlist to Insert Song Into
    Returns:
        int: unused return
    """
    utc_time = datetime.utcnow()
    lastUpdated = utc_time.strftime("%Y-%m-%d %H:%M:%S")

    models.PlaylistSongs.objects.filter(playlistID=playlist).delete()
    models.Playlists.objects.filter(
        playlistID=playlist).update(lastUpdated=lastUpdated)

    return 0


def add_playlist_songs(song: str, playlist: str, status: str):
    """
    Input Songs from Playlist into all PlayList Fields

    Parameters:
        playlist    (str)   : Which Playlist to Insert Song Into
        status      (str)   : local/playable/unplayable
    Returns:
        int: unused return
    """
    songExists = models.PlaylistSongs.objects.filter(
        songID=str(song.get("item").get("id")),
        playlistID=str(playlist)).count()

    if 0 == songExists:
        models.PlaylistSongs.objects.update_or_create(
            songStatus=status,
            songID=models.Songs.objects.get(
                id=str(song.get("item").get("id"))),
            playlistID=models.Playlists.objects.get(
                playlistID=str(playlist))
        )
    else:
        dataPlaylist = (
            playlist,
            song.get("item").get("id"),
            status
        )
        logging.warning("Duplicate Playlist Song: " +
                        str(dataPlaylist) + str(song.get("item").get("name")))
    return 0


def database_input(user: str, spotify: dict):
    """
    Input Songs into Database

    Parameters:
        user        (str): User ID
        spotify     (dict): Dictionary Containing Song Details
    Returns:
        bool: Dictionary Containing Song Details
    """
    add_artists(spotify)
    add_song(spotify)
    if(listening_history(user, spotify) == True):
        add_song_count(user, spotify)
    return spotify


def playlist_input(user: str, spotify: dict, playlist: str, status: str):
    """
    Input Songs from Playlist into all Database Fields

    Parameters:
        user        (str)   : User ID
        spotify     (dict)  : Dictionary Containing Song Details
        playlist    (str)   : Which Playlist to Insert Song Into
        status      (str)   : local/playable/unplayable
    Returns:
        int: unused return
    """
    spotify["item"] = spotify.get("track")
    if(spotify.get("item").get("is_local")):
        spotify["item"]["id"] = ":" + spotify.get("item").get("uri").replace("%2C", "").replace(
            "+", "").replace("%28", "").replace(":", "")[12:30] + spotify.get("item").get("uri")[-3:]
        for i in range(0, len(spotify.get("item").get("artists"))):
            spotify["item"]["artists"][i]["id"] = (
                (":" + (spotify.get("item").get("artists")[i].get("name"))).zfill(22))[:22]
    add_artists(spotify)
    add_song(spotify)
    add_song_count(user, spotify, 0)
    add_playlist_songs(spotify,  playlist, status)
    return 0
