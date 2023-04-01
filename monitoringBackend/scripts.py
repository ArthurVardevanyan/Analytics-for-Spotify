from django.db import connection
import webBackend.models as models
import logging
import sys
sys.path.append("..")

log = logging.getLogger(__name__)


def songIdUpdater(user: str):
    """
    Song ID Updater Helper Function

    Parameters:
        user   (str): User to Scan
    Returns:
        list: List of Changed Song IDs
    """
    history = getHistory(user)
    history = duplicateFinder(history)
    return databaseUpdate(history, user)


def getHistory(user: str):
    """
    Get Song History of User

    Parameters:
        user   (str): User to Scan
    Returns:
        list: List of Changed Song IDs
    """
    with connection.cursor() as cursor:
        query = 'SELECT played1.timestamp, songs.ID, songs.name, playCount.playCount, user\
                FROM songs\
                INNER JOIN playCount ON playCount.songID = songs.id\
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
            if(song[4] == user):
                history.append(song)
        logging.info("Total Songs: " + str(len(history)))
        songHistory = []
        for song in history:
            songL = list(song)
            songL.pop(4)
            if songL[0] == None:
                songL.pop(0)
                songL.insert(0, 990200212040000)
            query = 'SELECT songs_artists.songs_id, songs_artists.artists_id, artists.name from songs_artists \
            INNER JOIN artists on songs_artists.artists_id = artists.id\
            WHERE songs_artists.songs_id = ' + '"' + song[1] + '"'
            cursor.execute(query)
            artists = ''
            for artist in cursor:
                artists += artist[2] + ","
            songL.append(artists)
            songL.append(songL[2]+"_"+artists)
            songHistory.append(songL)
    return songHistory


def duplicateFinder(history: list):
    """
    Find Songs with Duplicate IDs

    Parameters:
        history   (list): Song History of User
    Returns:
        set: List of Song with Duplicate IDs
    """
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
    logging.info("Songs with new ID's: " + str(len(newHistory)))
    newHistory2 = []
    for item in newHistory:
        temp = item
        temp.sort(key=lambda i: i[0])
        newHistory2.append(tuple(temp))
    newHistory2 = set(newHistory2)
    logging.info("Songs with duplicate new ID's: " + str(len(newHistory2)))
    logging.info(newHistory2)
    return newHistory2


def databaseUpdate(history: set, user: str):
    """
    Get Song History of User

    Parameters:
        set: List of Song with Duplicate IDs
        user   (str): User to Scan
    Returns:
        list: List of updated songs.
    """
    trimmedHistory = []
    for song in history:
        newPlayCount = 0
        for item in song:
            newPlayCount += item[3]
        newID = song[len(song)-1][1]
        trimmedHistory.append(newID)
        oldIDS = []
        for i in range(0, len(song)-1):
            oldIDS.append(song[i][1])
        newSongID = models.Songs.objects.get(id=str(newID))
        userObject = models.Users.objects.get(user=str(user))
        models.PlayCount.objects.filter(
            songID=newSongID, user=userObject
        ).update(playCount=str(newPlayCount))

        for item in oldIDS:
            oldSongID = models.Songs.objects.get(id=str(item))
            models.ListeningHistory.objects.filter(
                songID=oldSongID, user=userObject).update(
                songID=newSongID
            )
            models.PlayCount.objects.filter(
                songID=oldSongID, user=userObject).delete()

            oldSongID.artists.clear()
            oldSongID.delete()
    return trimmedHistory


def main():
    # print(songIdUpdater(""))
    return 0


if __name__ == "__main__":
    main()
