import os
import base64
import binascii
import urllib.parse
import mysql.connector


def main():
    print("*Disclaimer*, DO NOT USE WITH PUBLIC ACCESS")
    DEBUG = input(
        "DEBUG Mode 0:OFF (For Production / Public Access), 1:ON (Self-Hosted / Testing):")
    if(DEBUG == 0):
        DEBUG = False
    else:
        DEBUG = True
    CLIENT = input("Enter Spotify Client Key:")
    SECRET = input("Enter Spotify Secret Key:")
    R_URL = input("Enter Spotify Redirect URL Key:")
    B64CS = str(base64.b64encode(
        ":".join([CLIENT, SECRET]).encode("utf-8")), "utf-8")
    SALT = str(binascii.hexlify(os.urandom(24)), "utf-8")
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
        "salt": SALT,
    }
    ENCRYPTION = 0
    PRIVATE_KEY = input(
        "0: None (Recommended for Self Hosted Internal Systems)\n1: Locally Stored Private Key\n3: Private Key Entered On WebServer Boot\nSet Encryption Level:")
    DJANGO_PRIVATE = str(binascii.hexlify(os.urandom(24)), "utf-8")
    PRIVATE = None
    if(ENCRYPTION):
        PRIVATE = str(binascii.hexlify(os.urandom(24)), "utf-8")
    ENV = [
        "D_DEBUG = " + str(DEBUG),
        "D_SECRET = '" + str(DJANGO_PRIVATE) + "'",
        "ENCRYPTION = " + str(ENCRYPTION),
        "PRIVATE = " + str(PRIVATE_KEY),
    ]
    with open("SpotifyAnalytics/env.py",  'w+') as f:
        f.writelines('\n'.join(ENV))

    print("MySql / MariaDB Integration")
    DB = input("Enter Database Name:")
    USER = input("Enter Username:")
    PASS = input("Enter Password:")
    MYSQL = [
        "[client]",
        "database = " + DB,
        "user = "+USER,
        "password = "+PASS,
        "default-character-set = utf8",
    ]
    with open("SpotifyAnalytics/my.cnf",  'w+') as f:
        f.writelines('\n'.join(MYSQL))

    db = mysql.connector.connect(
        host="localhost",
        user=USER,
        passwd=PASS,
        database=DB,
        auth_plugin='mysql_native_password'
    )
    cursor = db.cursor()
    add = ("INSERT IGNORE INTO spotifyAPI"
           "(clientID,api)"
           "VALUES (%s, %s)")
    data = (
        CLIENT,
        str(API),
    )
    cursor.execute(add, data)
    db.commit()
    db.close


if __name__ == "__main__":
    main()
