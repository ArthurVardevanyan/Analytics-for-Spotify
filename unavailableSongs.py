__version__ = "v20200329"


import requests
from authorization import authorization as authorize
import database


def main():
    print("Checking for Unavailable Songs")
    playlists = ""
    try:
        with open("credentials/playlists.txt") as f:
            playlists = f.readlines()
        playlists = [x.strip() for x in playlists]
    except:
        print("Credential Failure")

    url = 'https://api.spotify.com/v1/playlists/' + \
        playlists[0] + "/tracks?offset=0&limit=100&market=US"
    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + authorize()}

    playlistSections = []
    loop = True
    response = requests.get(url, headers=header)
    response = response.json()
    playlist = response
    database.add_playlist(playlist)

    playlistSections.append(response.get("tracks").get("items"))
    if response.get("tracks").get("next") == None:
        loop = False
    else:
        url = response.get("tracks").get("next")

    while(loop):
        response = requests.get(url, headers=header)
        response = response.json()
        playlistSections.append(response.get("items"))
        if response.get("next") == None:
            loop = False
        else:
            url = response.get("next")

    songs, localSongs,  unavailableSongs = seperator(
        playlistSections, playlist)
    for song in unavailableSongs:
        print("Unplayable: " + song.get("track").get("artists")[0].get(
            "name") + " - " + song.get("track").get("name"))


def seperator(playlistSections, playlist):
    songs = []
    localSongs = []
    unavailableSongs = []

    for section in playlistSections:
        for song in section:
            if song.get("is_local"):
                localSongs.append(song)
                database.playlist_input(song, playlist, "local")
            elif song.get("track").get("is_playable"):
                songs.append(song)
                database.playlist_input(song, playlist, "playable")
            else:
                unavailableSongs.append(song)
                database.playlist_input(song, playlist, "unplayable")

    return songs, localSongs, unavailableSongs


if __name__ == "__main__":
    main()
