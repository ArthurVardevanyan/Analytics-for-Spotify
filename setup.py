import os
import base64
import urllib.parse
import json
import tarfile
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AnalyticsForSpotify.settings")
django.setup()  # https://stackoverflow.com/a/74238820


def extractNode():
    """
    Extracts Node Modules, only used when running outside of a container.

    Parameters:
        None
    Returns:
        int: unused return
    """
    with tarfile.open("webFrontend/node_modules.tar.xz", 'r') as tar:
        tar.extractall("webFrontend/")

    return 0


def spotifyAPI(CLIENT: str, SECRET: str, R_URL: str):
    """
    Setup Spotify Configuration for Injection into to DB

     Parameters:
        CLIENT  (str)   : Spotify Client ID
        SECRET  (str)   : Spotify Client Secret
        R_URL   (str)   : Spotify Redirect URL
    Returns:
        dict: Dictionary Containing Spotify API Configuration
    """
    B64CS = str(base64.b64encode(
        ":".join([CLIENT, SECRET]).encode("utf-8")), "utf-8")
    SCOPES = "&scope=user-read-currently-playing+user-read-recently-played"
    URL = "https://accounts.spotify.com/authorize?client_id=" + CLIENT + \
        "&response_type=code&redirect_uri=" + \
        urllib.parse.quote_plus(R_URL) + SCOPES
    API = {
        "client": CLIENT,
        "secret": SECRET,
        "B64CS": B64CS,
        "url": URL,
        "redirect_url": R_URL,
    }
    return API


def setup(API: dict):
    from django.db import connection
    from webBackend.models import SpotifyAPI

    """
    If new Instance, sets up the database, and injects API Config.
    If existing Instance, updates the API Config.

    Parameters:
        db   (MySQLdb): Database Connection Object
        API  (dict)   : Spotify API Configuration

    Returns:
        int: unused return
    """

    if not (len(connection.introspection.table_names())):
        os.system("python3 manage.py migrate")

    SpotifyAPI.objects.all()
    SpotifyAPI.objects.all().delete()
    SpotifyAPI.objects.create(api=json.dumps(API))

    return 0


def main():
    """
    Init Setup Script before loading Application,
    setups database initial database,
    and injects Spotify API Credentials

    Supports Manually Inputting Parameters,
    or pulling from the environment.

     Parameters:
        CLIENT  (str)   : Spotify Client ID
        SECRET  (str)   : Spotify Client Secret
        R_URL   (str)   : Spotify Redirect URL

    Returns:
        bool: Script Exit Condition
    """
    print("*Disclaimer*, DO NOT USE WITH PUBLIC ACCESS")

    CLIENT = os.environ.get('CLIENT_ID')
    SECRET = os.environ.get('CLIENT_SECRET')
    R_URL = os.environ.get('REDIRECT_URL')
    API = spotifyAPI(CLIENT, SECRET, R_URL)

    setup(API)

    return 0


if __name__ == "__main__":
    main()
