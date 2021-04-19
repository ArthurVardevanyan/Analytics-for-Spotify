import mysql.connector
import json
from datetime import datetime, timezone
import sys

# WARNING, DO NOT RUN IN MULTI USER ENVIRONMENTS, THIS SCRIPT CURRENTLY ONLY WORKS FOR SINGLE USER ENVIRONMENTS.


def songIdUpdater():
    db = {}
    with open("AnalyticsforSpotify/my.cnf") as f:
        count = 0
        for line in f:
            if not (count == 0 or count == 5):
                line = line.rstrip().replace(" ", "")
                (key, val) = line.split('=')
                db[key] = val
            count += 1

    connection = mysql.connector.connect(
        host=db['host'],
        user=db['user'],
        passwd=db['password'],
        database=db['database'],
        auth_plugin='mysql_native_password'
    )

    history = getHistory(connection)
    history = duplicateFinder(history)
    databaseUpdate(history, connection)


def getHistory(connection):

    with connection.cursor() as cursor:
        query = 'SELECT played1.timestamp, songs.ID, songs.name, playcount.playCount\
                FROM songs\
                INNER JOIN playcount ON playcount.songID = songs.id\
                LEFT JOIN (\
                SELECT `songID`, `timestamp`\
                FROM(SELECT `songID`, `timestamp`,\
                (ROW_NUMBER() OVER (PARTITION BY songID ORDER BY timestamp DESC)) as rn\
                FROM `listeningHistory`  )\
                AS played0 WHERE `rn` = 1  ORDER BY `played0`.`timestamp`  ASC )\
                AS played1 ON played1.songID = songs.id'
        cursor.execute(query)

        history = []
        for song in cursor:
            history.append(song)
        print(len(history))
        songHistory = []
        for song in history:
            songL = list(song)
            if songL[0] == None:
                songL.pop(0)
                songL.insert(0, 990200212040000)
            query = 'SELECT songArtists.songID, songArtists.artistID, artists.name from songArtists \
            INNER JOIN artists on songArtists.artistID = artists.id\
            WHERE songArtists.songID = ' + '"' + song[1] + '"'
            cursor.execute(query)
            artists = ''
            for artist in cursor:
                artists += artist[2] + ","
            songL.append(artists)
            songL.append(songL[2]+"_"+artists)
            songHistory.append(songL)
    return songHistory


def duplicateFinder(history):
    history.sort(key=lambda i: i[5])
    newHistory = []
    for i in reversed(range(0, len(history))):
        temp = []
        dup = 0
        for j in reversed(range(0, len(history))):
            if (history[i][5] == history[j][5]):
                if (i != j):
                    dup = 1
                    temp.append(tuple(history[j]))
        if (dup == 1):
            temp.append(tuple(history[i]))
            newHistory.append(temp)
    print(len(newHistory))
    newHistory2 = []
    for item in newHistory:
        temp = item
        temp.sort(key=lambda i: i[0])
        newHistory2.append(tuple(temp))
    newHistory2 = set(newHistory2)
    print(len(newHistory2))
    return newHistory2


def databaseUpdate(history, connection):
    for song in history:
        newPlayCount = 0
        for item in song:
            newPlayCount += item[3]
        newID = song[len(song)-1][1]
        oldIDS = []
        for i in range(0, len(song)-1):
            oldIDS.append(song[i][1])
        with connection.cursor() as cursor:
            query = "UPDATE `playcount` SET `playCount`=" + \
                str(newPlayCount) + " WHERE `songID` ='" + newID + "'"
            cursor.execute(query)
            for item in oldIDS:
                query = "UPDATE `listeningHistory` SET `songID`='" + \
                    newID + "' WHERE `songID` ='" + item + "'"
                cursor.execute(query)
                query = "DELETE FROM `playcount` WHERE `songID` ='" + item + "'"
                cursor.execute(query)
                query = "DELETE FROM `songArtists` WHERE `songID` ='" + item + "'"
                cursor.execute(query)
                query = "DELETE FROM `songs` WHERE `id` ='" + item + "'"
                cursor.execute(query)
    connection.commit()
    return history


def main():
    # This Script is WIP, use at own risk. Ensure proper backups.
    # songIdUpdater()
    return 1


if __name__ == "__main__":
    main()
