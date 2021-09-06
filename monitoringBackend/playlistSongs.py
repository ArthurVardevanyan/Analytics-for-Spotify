import requests
import sys
import logging
sys.path.append("..")
from webBackend.credentials import refresh_token as authorize
import monitoringBackend.database as database

log = logging.getLogger(__name__)


def main(user, playlist):
    logging.info("Checking for Playlist Songs: " +
                 str(user) + " " + str(playlist))
    playlist = playlist[0]
    url = ""
    try:
        url = 'https://api.spotify.com/v1/playlists/' + \
            playlist + "/tracks?offset=0&limit=100&market=US"
    except:
        logging.exception("Playlist Reterival Failure")
        return False

    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + authorize(user)}
    playlistSections = []
    loop = True
    response = requests.get(url, headers=header).json()
    database.add_playlist(user, playlist)
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

    for section in playlistSections:
        for song in section:
            if song.get("is_local"):
                database.playlist_input(user, song, playlist, "local")
            elif song.get("track").get("is_playable"):
                database.playlist_input(user, song, playlist, "playable")
            else:
                database.playlist_input(user, song, playlist, "unplayable")
    return True


if __name__ == "__main__":
    main()
