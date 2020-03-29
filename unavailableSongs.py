__version__ = "v20200328"


import requests
from authorization import authorization as authorize


def main():

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

    songs, localSongs,  unavailableSongs = seperator(playlistSections)
    for song in unavailableSongs:
        print(song.get("track").get("artists")[0].get(
            "name") + " - " + song.get("track").get("name"))


def seperator(playlistSections):
    songs = []
    localSongs = []
    unavailableSongs = []
    for section in playlistSections:
        for song in section:
            if song.get("is_local"):
                localSongs.append(song)
            elif song.get("track").get("is_playable"):
                songs.append(song)
            else:
                unavailableSongs.append(song)

    return songs, localSongs, unavailableSongs


if __name__ == "__main__":
    main()
