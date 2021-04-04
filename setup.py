import os
import base64
import binascii
import urllib.parse
import mysql.connector
import json
import zipfile


def unzip():
    with zipfile.ZipFile("webFrontend/node_modules.zip", 'r') as zip_ref:
        zip_ref.extractall("webFrontend/")


def executeScriptsFromFile(c, filename):
    # https://stackoverflow.com/a/19473206
    # Open and read the file as a single buffer
    fd = open(filename, 'r')
    sqlFile = fd.read()
    fd.close()

    # all SQL commands (split on ';')
    sqlCommands = sqlFile.split(';')

    # Execute every command from the input file
    for command in sqlCommands:
        # This will skip and report errors
        # For example, if the tables do not yet exist, this will skip over
        # the DROP TABLE commands
        try:
            c.execute(command)
        except:
            continue


def main():
    print("*Disclaimer*, DO NOT USE WITH PUBLIC ACCESS")  
    unzip()
    CLIENT = input("Enter Spotify Client Key:")
    SECRET = input("Enter Spotify Secret Key:")
    R_URL = input("Enter Spotify Redirect URL Key:")
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
    
    print("MySql / MariaDB Integration")
    IP = input("Enter Database IP or (localhost):")
    DB = input("Enter Database Name:")
    USER = input("Enter Username:")
    PASS = input("Enter Password:")
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

    print("Finalizing Django Setup")
    os.system("python3 manage.py migrate")


if __name__ == "__main__":
    main()
