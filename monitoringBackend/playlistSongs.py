import monitoringBackend.database as database
from webBackend.credentials import refresh_token as authorize
import requests
import time
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
    except Exception:
        logging.exception("Playlist Retrieval Failure")
        return False

    try:
        token = authorize(user)
        if not token:
            log.warning("Playlist: revoked/invalid token for %s, skipping until next cycle", user)
            return False
        header = {"Accept": "application/json",
                  "Content-Type": "application/json", "Authorization": "Bearer " + token}
    except Exception:
        log.exception("Playlist: authorize failed for %s", user)
        database.reset_db_connection()
        return False

    playlistSections = []
    loop = True
    try:
        response = requests.get(url, headers=header).json()
    except Exception:
        logging.exception("Playlist: API request failed for %s", user)
        database.reset_db_connection()
        return False

    database.add_playlist(playlist)
    playlistSections.append(response.get("items"))
    if response.get("next") is None:
        loop = False
    else:
        url = response.get("next")

    while(loop):
        try:
            response = requests.get(url, headers=header).json()
        except Exception:
            log.warning("Playlist: API pagination request failed, retrying")
            time.sleep(60)
            try:
                response = requests.get(url, headers=header).json()
            except Exception:
                log.exception("Playlist: API pagination failed after retry")
                database.reset_db_connection()
                return False
        playlistSections.append(response.get("items"))
        if response.get("next") is None:
            loop = False
        else:
            url = response.get("next")

    playListDB = []
    for section in playlistSections:
        if section is not None:
            for song in section:
                if song is not None and song.get("track") is not None:
                    if song.get("is_local"):
                        playListDB.append((song, "local"))
                    elif song.get("track").get("is_playable"):
                        playListDB.append((song, "playable"))
                    else:
                        playListDB.append((song, "unplayable"))

    try:
        database.playlist_input(user, playlist, playListDB)
    except Exception:
        log.exception("Playlist: DB input failed for %s", user)
        database.reset_db_connection()
        return False

    return True


if __name__ == "__main__":
    main()
