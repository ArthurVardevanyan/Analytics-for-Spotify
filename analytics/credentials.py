from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
import json
import requests
import time
import database
import hashlib
import cryptography
from cryptography.fernet import Fernet
import ast
from SpotifyAnalytics.env import ENCRYPTION
key = []
API = ""
f = ""


def decryptPlaylist(e):
    if(ENCRYPTION):
        return str(f.decrypt(e).decode("utf-8"))
    else:
        return str(e.decode("utf-8"))


def encryptContent(e):
    # thepythoncode.com/article/encrypt-decrypt-files-symmetric-python
    if(ENCRYPTION):
        return (f.encrypt(str(e).encode())).decode("utf-8")
    else:
        return str(e)


def decryptUserJson(userID):
    userData = ""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from users  WHERE user = '" + userID + "'")
        for user in cursor:
            userData = user
    if(ENCRYPTION):
        return ast.literal_eval((f.decrypt(userData[4]).decode("utf-8")))
    else:
        return ast.literal_eval(userData[4].decode("utf-8"))


def apiDecrypt():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from spotifyAPI")
        for api in cursor:
            if(ENCRYPTION):
                return ast.literal_eval((f.decrypt(api[0]).decode("utf-8")))
            else:
                return ast.literal_eval((api[0]).decode("utf-8"))


def refresh_token(userID):
    # Checks For and Provides Refresh Token
    access = ''
    access = decryptUserJson(userID)
    if(int(time.time()) >= access["expires_at"]):
        header = {"Authorization": "Basic " + API.get("B64CS")}
        data = {"grant_type": "refresh_token",
                "refresh_token": access.get("refresh_token"),
                "redirect_uri": "http://localhost/analytics/loginResponse"}
        auth = requests.post(
            'https://accounts.spotify.com/api/token', headers=header, data=data).json()
        expire = auth.get("expires_in")
        auth["expires_at"] = int(time.time()) + expire
        auth["refresh_token"] = auth.get(
            "refresh_token", access.get("refresh_token"))
        cache = encryptContent(auth)
        cursor = connection.cursor()
        query = 'UPDATE users SET cache = "'+cache+'" WHERE user = "' + userID + '"'
        cursor.execute(query)
        return auth.get("access_token")
    else:
        return access.get("access_token")
