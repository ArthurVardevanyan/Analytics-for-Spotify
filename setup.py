import os
import base64
import binascii
import urllib.parse
import json
import tarfile
import MySQLdb


def extractNode():
    with tarfile.open("webFrontend/node_modules.tar.xz", 'r') as tar:
        tar.extractall("webFrontend/")


def dockerSetup():
    CLIENT = os.environ.get('CLIENT_ID')
    SECRET = os.environ.get('CLIENT_SECRET')
    R_URL = os.environ.get('REDIRECT_URL')
    API = spotifyAPI(CLIENT, SECRET, R_URL)

    IP = os.environ.get('HOST')
    DB = os.environ.get('DATABASE')
    USER = os.environ.get('DB_USER')
    PASS = os.environ.get('DB_PASSWORD')

    db = myCNF(IP, DB, USER, PASS)
    setup(db, API)

    # Check if thier are users in the database, mark as disabled, run manage, then re-enable.


def myCNF(IP, DB, USER, PASS):
    MYSQL = [
        "[client]",
        "host = " + IP,
        "database = " + DB,
        "user = "+USER,
        "password = "+PASS,
        "default-character-set = utf8",
    ]

    db = MySQLdb.connect(
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
    cursor = db.cursor()
    users = 'show tables like "users"'
    cursor.execute(users)
    count = 0
    for user in cursor:
        count += 1

    if(not count):
        os.system("python3 manage.py migrate")

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
        CLIENT = input("Enter Spotify Client ID    :")
        SECRET = input("Enter Spotify Client Secret:")
        R_URL = input("Enter Spotify Redirect URL :")
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
