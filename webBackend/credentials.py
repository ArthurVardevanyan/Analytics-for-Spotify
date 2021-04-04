from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
import json
import requests
import time


def getUserJson(userID):
    userData = ""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from users  WHERE user = '" + userID + "'")
        for user in cursor:
            userData = user
    return json.loads(userData[4])


def getUser(auth):
    url = "https://api.spotify.com/v1/me"
    header = {"Accept": "application/json",
              "Content-Type": "application/json", "Authorization": "Bearer " + auth.get("access_token")}
    result = requests.get(url,
                          headers=header).json().get("id")
    return result


def getAPI():
    with connection.cursor() as cursor:
        cursor.execute("SELECT `api` from spotifyAPI")
        for api in cursor:
            return json.loads(api[0])


def refresh_token(userID):
    # Checks For and Provides Refresh Token
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
        cursor = connection.cursor()
        query = """UPDATE users SET cache = '""" + \
            json.dumps(auth) + """' WHERE user = '""" + userID + "'"
        query = query.replace("\\", "")
        cursor.execute(query)
        return auth.get("access_token")
    else:
        return access.get("access_token")


def accessToken(request, CODE):
    header = {"Authorization": "Basic " + getAPI().get("B64CS")}
    data = {
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": getAPI().get("redirect_url")}
    response = requests.post(
        'https://accounts.spotify.com/api/token', headers=header, data=data)
    auth = response.json()
    currentTime = int(time.time())
    expire = auth.get("expires_in")
    auth["expires_at"] = currentTime + expire
    userID = ""
    userID = getUser(auth)
    request.session['spotify'] = userID  # SESSION
    query = 'INSERT IGNORE INTO users (`user`, `enabled`, `statusSong`, `statusPlaylist`, `realTime`, `cache`) VALUES ("' + \
        userID + '", 0, 0, 0, 1,' + "'" + json.dumps(auth) + "')"
    cursor = connection.cursor()
    cursor.execute(query)
    query = "UPDATE users SET cache = '" + \
        json.dumps(auth) + "' WHERE user = '" + userID + "'"
    cursor.execute(query)
    return True
