import os
import base64
import binascii
import urllib.parse
import mysql.connector
import json
import tarfile


def extractNode():
    with tarfile.open("webFrontend/node_modules.tar.xz", 'r') as tar:
        tar.extractall("webFrontend/")


def dockerSetup():
    CLIENT = os.environ.get('CLIENT_ID')
    SECRET = os.environ.get('CLIENT_SECERT')
    R_URL = os.environ.get('REDIRECT_URL')
    API = spotifyAPI(CLIENT, SECRET, R_URL)

    IP = os.environ.get('HOST')
    DB = os.environ.get('DATABASE')
    USER = os.environ.get('USER')
    PASS = os.environ.get('PASSWORD')

    db = myCNF(IP, DB, USER, PASS)
    setup(db, API)


def myCNF(IP, DB, USER, PASS):
    MYSQL = [
        "[client]",
        "host = " + IP,
        "database = " + DB,
        "user = "+USER,
        "password = "+PASS,
        "default-character-set = utf8",
    ]
    with open("AnalyticsforSpotify/my.cnf",  'w+') as f:
        f.writelines('\n'.join(MYSQL))
    db = mysql.connector.connect(
        host=IP,
        user=USER,
        passwd=PASS,
        database=DB,
        auth_plugin='mysql_native_password'
    )
    return db


def spotifyAPI(CLIENT, SECRET, R_URL):
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


def setup(db, API):
    os.system("python3 manage.py migrate")

    cursor = db.cursor()
    delete = "DELETE FROM `spotifyAPI` WHERE 1"
    cursor.execute(delete)
    add = ("INSERT IGNORE INTO spotifyAPI"
           "(api)"
           "VALUES (%s)")
    data = (
        json.dumps(API),
    )
    cursor.execute(add, data)
    db.commit()
    db.close


def main():
    print("*Disclaimer*, DO NOT USE WITH PUBLIC ACCESS")
    if(os.environ.get('DOCKER')):
        dockerSetup()
    else:
        extractNode()
        CLIENT = input("Enter Spotify Client Key:")
        SECRET = input("Enter Spotify Secret Key:")
        R_URL = input("Enter Spotify Redirect URL Key:")
        API = spotifyAPI(CLIENT, SECRET, R_URL)

        print("MySql / MariaDB Integration")
        IP = input("Enter Database IP or (localhost):")
        DB = input("Enter Database Name:")
        USER = input("Enter Username:")
        PASS = input("Enter Password:")
        db = myCNF(IP, DB, USER, PASS)
        setup(db, API)


if __name__ == "__main__":
    main()
