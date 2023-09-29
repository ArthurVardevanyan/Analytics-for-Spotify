import monitoringBackend.database as database
from webBackend.credentials import refresh_token as authorize
import requests
import sys
import logging
sys.path.append("..")

log = logging.getLogger(__name__)


def main(user: str, playlist: str):
    """
    Playlist Song Controller

    Parameters:
        user        (str): User ID
        playlist    (str)   : Which Playlist to Insert Song Into
    Returns:
        bool: unused return
    """
    logging.info("Checking for Playlist Songs: " +
                 str(user) + " " + str(playlist))
    playlist = playlist[0]
    url = ""
    try:
        url = 'https://api.spotify.com/v1/playlists/' + \
            playlist + "/tracks?offset=0&limit=100&market=US"
    except:
        logging.exception("Playlist Retrieval Failure")
        return False

    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
    playlistSections = []
    loop = True
    response = requests.get(url, headers=header).json()
    database.add_playlist(playlist)
    playlistSections.append(response.get("items"))
    if response.get("next") == None:
        loop = False
    else:
        url = response.get("next")

    while(loop):
        response = requests.get(url, headers=header).json()
        playlistSections.append(response.get("items"))
        if response.get("next") == None:
            loop = False
        else:
            url = response.get("next")

    playListDB = []
    for section in playlistSections:
        if section != None:
            for song in section:
                if song.get("track") != None:
                    if song.get("is_local"):
                        playListDB.append((song, "local"))
                    elif song.get("track").get("is_playable"):
                        playListDB.append((song, "playable"))
                    else:
                        playListDB.append((song, "unplayable"))

    database.playlist_input(user, playlist, playListDB)

    return True


if __name__ == "__main__":
    main()
