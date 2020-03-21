__version__ = "v20200320"

import pprint
import sys
import os
import subprocess

import spotipy
import spotipy.util as util

# https://stackoverflow.com/questions/42743405/spotify-api-authentication-via-command-line
# https://spotipy.readthedocs.io/en/latest/

key = []
try:
    with open("credentials/spotifyCredentials.txt") as f:
        key = f.readlines()
    key = [x.strip() for x in key]
except:
    print("Credential Failure")


def authorization():
    client_id = key[0]
    client_secret = key[1]
    redirect_uri = 'http://localhost:80'
    username = key[2]
    scope = 'user-read-currently-playing'

    token = util.prompt_for_user_token(
        username, scope, client_id, client_secret, redirect_uri)
    sp = spotipy.Spotify(auth=token)
    return sp._auth


if __name__ == "__main__":
    authorization()
