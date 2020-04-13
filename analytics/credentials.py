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
key = []
API = ""
f = ""


def encryptJson(auth):
    # thepythoncode.com/article/encrypt-decrypt-files-symmetric-python
    return (f.encrypt(str(auth).encode())).decode("utf-8")


def decryptUserJson(userID):
    userData = ""
    with connection.cursor() as cursor:
        users = "SELECT * from users  WHERE user = '" + userID + "'"
        cursor.execute(users)
        for user in cursor:
            userData = user
    return ast.literal_eval((f.decrypt(userData[4]).decode("utf-8")))


def apiDecrypt():
    with connection.cursor() as cursor:
        api = "SELECT * from spotifyAPI"
        cursor.execute(api)
        for api in cursor:
            return ast.literal_eval((f.decrypt(api[0]).decode("utf-8")))


def refresh_token(userID):
    # Checks For and Provides Refresh Token
    access = ''
    access = decryptUserJson(userID)
    if(int(time.time()) >= access["expires_at"]):
        header = {"Authorization": "Basic " + API.get("B64CS")}
        data = {"grant_type": "refresh_token",
                "refresh_token": access.get("refresh_token"),
                "redirect_uri": "http://localhost/analytics/loginResponce"}
        response = requests.post(
            'https://accounts.spotify.com/api/token', headers=header, data=data)
        auth = response.json()
        currentTime = int(time.time())
        expire = auth.get("expires_in")
        auth["expires_at"] = currentTime + expire
        auth["refresh_token"] = auth.get(
            "refresh_token", access.get("refresh_token"))
        cache = encryptJson(auth)
        cursor = connection.cursor()
        query = "UPDATE users SET cache = '"+cache+"' WHERE user = '" + userID + "'"
        cursor.execute(query)
        return auth.get("access_token")
    else:
        return access.get("access_token")
