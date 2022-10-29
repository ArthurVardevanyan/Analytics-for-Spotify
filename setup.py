import os
import base64
import urllib.parse
import json
import tarfile
import MySQLdb


def extractNode():
    """
    Extracts Node Modules, only used when running outside of a container.

    Parameters:
        None
    Returns:
        bool: unused return
    """
    with tarfile.open("webFrontend/node_modules.tar.xz", 'r') as tar:
        tar.extractall("webFrontend/")

    return 0


def containerSetup():
    """
    Pull Setup Variables from Environment,
    and setup setup container runtime configs.

     Parameters:
        CLIENT  (str)   : Spotify Client ID
        SECRET  (str)   : Spotify Client Secret
        R_URL   (str)   : Spotify Redirect URL

        IP      (str)   : Database IP / Hostname
        DB      (str)   : Database Name
        USER    (str)   : Database Username
        PASS    (str)   : Database Password
    Returns:
        bool: unused return
    """
    CLIENT = os.environ.get('CLIENT_ID')
    SECRET = os.environ.get('CLIENT_SECRET')
    R_URL = os.environ.get('REDIRECT_URL')
    API = spotifyAPI(CLIENT, SECRET, R_URL)

    IP = os.environ.get('DB_HOST')
    DB = os.environ.get('DATABASE')
    USER = os.environ.get('DB_USER')
    PASS = os.environ.get('DB_PASSWORD')

    db = myCNF(IP, DB, USER, PASS)
    setup(db, API)

    # TODO: Check if their are users in the database, mark as disabled, run manage, then re-enable.

    return 0


def myCNF(IP: str, DB: str, USER: str, PASS: str):
    """
    Creates an MySQL Connection Object

    Parameters:
        IP      (str)   : Database IP / Hostname
        DB      (str)   : Database Name
        USER    (str)   : Database Username
        PASS    (str)   : Database Password
    Returns:
        MySQLdb: MySQL Connection Object
    """
    db = MySQLdb.connect(
        host=IP,
        user=USER,
        passwd=PASS,
        database=DB,
        auth_plugin='mysql_native_password'
    )
    return db


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


def setup(db: MySQLdb.connections, API: dict):
    """
    If new Instance, sets up the database, and injects API Config.
    If existing Instance, updates the API Config.

    Parameters:
        db   (MySQLdb): Database Connection Object
        API  (dict)   : Spotify API Configuration

    Returns:
        bool: unused return
    """
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

        IP      (str)   : Database IP / Hostname
        DB      (str)   : Database Name
        USER    (str)   : Database Username
        PASS    (str)   : Database Password
    Returns:
        bool: Script Exit Condition
    """
    print("*Disclaimer*, DO NOT USE WITH PUBLIC ACCESS")
    if(os.environ.get('DOCKER')):
        containerSetup()
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

    return 0


if __name__ == "__main__":
    main()
