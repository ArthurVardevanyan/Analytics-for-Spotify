import webBackend.models as models
import requests
import json
import time


def getUserJson(userID: str):
    """
    Gets User JSON from Database.

    Parameters:
        userID        (str): User ID
    Returns:
        dict: User Json
    """
    return json.loads(models.Users.objects.get(user=str(userID)).cache)


def getUser(auth: dict):
    """
    Gets User from Spotify API from Auth Object

    Parameters:
        auth    (dict): Spotify Auth Object
    Returns:
        str: UserID
    """
    url = "https://api.spotify.com/v1/me"
    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + auth.get("access_token")}
    result = requests.get(url,
                          headers=header).json().get("id")
    return result


def getAPI():
    """
    Gets User from Spotify API from Auth Object

    Parameters:
        userID        (str): User ID
    Returns:
        dict: Spotify API Configuration
    """
    return json.loads(models.SpotifyAPI.objects.get().api)


def refresh_token(userID: str):
    """
    Checks For and Provides Refresh Token

    Parameters:
        None
    Returns:
        str: Access Token
    """
    access = ''
    access = getUserJson(userID)
    if(int(time.time()) >= access["expires_at"]):
        header = {"Authorization": "Basic " + getAPI().get("B64CS")}
        data = {"grant_type": "refresh_token",
                "refresh_token": access.get("refresh_token"),
                "redirect_uri": "http://localhost/analytics/loginResponse"}
        auth = requests.post(
            'https://accounts.spotify.com/api/token', headers=header, data=data).json()
        expire = auth.get("expires_in")
        auth["expires_at"] = int(time.time()) + expire
        auth["refresh_token"] = auth.get(
            "refresh_token", access.get("refresh_token"))
        models.Users.objects.filter(
            user=str(userID)).update(cache=json.dumps(auth))
        return auth.get("access_token")
    else:
        return access.get("access_token")


def accessToken(CODE: str):
    """
    Access Token from Authorization Code

    Parameters:
        CODE:   (str): Authorization Code
    Returns:
        dict: Spotify Auth Object
    """
    header = {"Authorization": "Basic " + getAPI().get("B64CS")}
    data = {
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": getAPI().get("redirect_url")}
    response = requests.post(
        'https://accounts.spotify.com/api/token', headers=header, data=data)
    return response.json()


def setSession(request: requests.request, CODE: str):
    """
    Access Token from Authorization Code

    Parameters:
        request:    (request)   : Request Object
        CODE:       (str)       : Authorization Code
    Returns:
        bool: Unused Return
    """
    auth = accessToken(CODE)
    currentTime = int(time.time())
    expire = auth.get("expires_in")
    auth["expires_at"] = currentTime + expire
    userID = ""
    userID = getUser(auth)
    request.session['spotify'] = userID  # SESSION
    try:
        models.Users.objects.get(user=str(userID))
        models.Users.objects.filter(
            user=str(userID)).update(cache=json.dumps(auth))
    except:
        models.Users.objects.create(
            user=str(userID),
            enabled=0,
            statusSong=0,
            statusPlaylist=0,
            realtime=0,
            cache=json.dumps(auth))
    return True
