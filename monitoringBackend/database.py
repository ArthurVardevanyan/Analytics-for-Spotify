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
    count = 0

    try:
        models.Workers.objects.filter(worker=str(workerID)).update(
         lastUpdated=str(currentEpoch), updatedTime=str(utc_time.strftime("%Y-%m-%d %H:%M:%S")))
    except:
        log.exception("Scan Worker DB Error")
        return -1

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


def add_artists(spotify: dict, playlist: bool = False):
    """
    Add Artist to Artist List

    Parameters:
        spotify     (dict)  : Dictionary Containing Song Details
    Returns:
        int: unused return
    """
    artistBulkCreate = []
    artistBulkUpdate = []
    for iter in spotify.get("item").get("artists"):
        artist = str(iter.get("name"))
        try:
            model = models.Artists.objects.get(id=iter.get("id"))
            model.name = artist
            if playlist:
                artistBulkUpdate.append(model)
            else:
                model.save(update_fields=['name'])
        except models.Artists.DoesNotExist:
            model = models.Artists(id=iter.get("id"), name=artist)
            if playlist:
                artistBulkCreate.append(model)
            else:
                model.save()

    if playlist:
        return artistBulkCreate, artistBulkUpdate
    else:
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


def add_song_count(user: str, spotify: dict, count: int = 1, playlist: bool = False, songObject: models.Songs = None, userObject: models.Users = None):
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
    if songObject == None:
        songID = models.Songs.objects.get(id=str(song))
    else:
        songID = songObject
    if songObject == None:
        userObject = models.Users.objects.get(user=str(user))
    else:
        userObject = userObject

    createModel = None
    updateModel = None

    try:
        updateModel = models.PlayCount.objects.get(
            songID=songID,
            user=userObject
        )
        updateModel.playCount = str(int(updateModel.playCount) + count)
        if not playlist:
            updateModel.save(update_fields=['playCount'])

    except models.PlayCount.DoesNotExist:
        createModel = models.PlayCount(
            user=userObject,
            songID=songID,
            playCount=count
        )
        if not playlist:
            createModel.save()
            # Temp# TODO: Bulk Input Support
            add_song_artists(spotify, songID)

    if playlist:
        return createModel, updateModel
    else:
        return 0


def add_song(spotify: dict, playlist: bool = False):
    """
    Add Song to Song List

    Parameters:
        spotify     (dict)  : Dictionary Containing Song Details
    Returns:
        int: unused return
    """

    songID = spotify.get("item").get("id")
    name = spotify.get("item").get("name"),
    trackLength = spotify.get("item").get("duration_ms")

    createModel = None
    updateModel = None

    try:
        updateModel = models.Songs.objects.get(id=songID)
        updateModel.name = name[0]
        updateModel.trackLength = trackLength
        if not playlist:
            updateModel.save(update_fields=['name', 'trackLength'])
            add_song_artists(spotify, updateModel)  # TODO: Bulk Input Support
    except models.Songs.DoesNotExist:
        createModel = models.Songs(
            id=songID, name=name[0], trackLength=trackLength)
        if not playlist:
            createModel.save()
            # Temp# TODO: Bulk Input Support
            add_song_artists(spotify, createModel)

    if playlist:
        return createModel, updateModel
    else:
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


def add_playlist_songs(song: str, playlistObject: models.Playlists, status: str, songObject: models.Songs = None):
    """
    Input Songs from Playlist into all PlayList Fields

    Parameters:
        playlist    (str)   : Which Playlist to Insert Song Into
        status      (str)   : local/playable/unplayable
    Returns:
        int: unused return
    """
    songID = str(song.get("item").get("id"))
    if songObject == None:
        songObject = models.Songs.objects.get(id=songID)

    createModel = None

    try:
        models.PlaylistSongs.objects.get(
            songID=songObject, playlistID=playlistObject)
        dataPlaylist = (playlistObject.playlistID, songID, status)
        logging.warning("Duplicate Playlist Song: " +
                        str(dataPlaylist) + str(song.get("item").get("name")))
    except models.PlaylistSongs.DoesNotExist:
        createModel = models.PlaylistSongs(
            songStatus=status,
            songID=songObject,
            playlistID=playlistObject
        )

    return createModel


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


def playlist_input(user: str, playlist: str, playlistDB: list):
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
    artistDB = []
    songDB = []
    playCountDB = []
    playListSongsDB = []

    userObject = models.Users.objects.get(user=str(user))
    playlistObject = models.Playlists.objects.get(playlistID=playlist)

    for song in playlistDB:
        spotify = song[0]
        status = song[1]
        spotify["item"] = spotify.get("track")
        if(spotify.get("item").get("is_local")):
            spotify["item"]["id"] = ":" + spotify.get("item").get("uri").replace("%2C", "").replace(
                "+", "").replace("%28", "").replace(":", "")[12:30] + spotify.get("item").get("uri")[-3:]
            for i in range(0, len(spotify.get("item").get("artists"))):
                spotify["item"]["artists"][i]["id"] = (
                    (":" + (spotify.get("item").get("artists")[i].get("name"))).zfill(22))[:22]

        artistDB.append(add_artists(spotify, True))

        songTuple = add_song(spotify, True)
        if songTuple[0] != None:
            songObject = songTuple[0]
        else:
            songObject = songTuple[1]
        songDB.append(songTuple)

        playCountDB.append(add_song_count(
            user, spotify, count=0, playlist=True, songObject=songObject, userObject=userObject))
        playListSongsDB.append(add_playlist_songs(
            spotify,  playlistObject, status, songObject))

    artistCreate = []
    artistUpdate = []
    for song in artistDB:
        for artist in song[0]:
            artistCreate.append(artist)
        for artist in song[1]:
            artistUpdate.append(artist)

    models.Artists.objects.bulk_create(artistCreate, ignore_conflicts=True)
    models.Artists.objects.bulk_update(artistUpdate, ['name'])

    songCreate = []
    songUpdate = []
    for song in songDB:
        if song[0] != None:
            songCreate.append(song[0])
        if song[1] != None:
            songUpdate.append(song[1])

    models.Songs.objects.bulk_create(songCreate, ignore_conflicts=True)
    models.Songs.objects.bulk_update(songUpdate, ['name', 'trackLength'])

    playCountCreate = []
    playCountUpdate = []
    for playCount in playCountDB:
        if playCount[0] != None:
            playCountCreate.append(playCount[0])
        if playCount[1] != None:
            playCountUpdate.append(playCount[1])

    models.PlayCount.objects.bulk_create(
        playCountCreate, ignore_conflicts=True)
    models.PlayCount.objects.bulk_update(
        playCountUpdate, ['playCount'])

    playListSongCreate = []
    for playListSong in playListSongsDB:
        if playListSong != None:
            playListSongCreate.append(playListSong)

    models.PlaylistSongs.objects.bulk_create(
        playListSongCreate, ignore_conflicts=True)

    return 0
