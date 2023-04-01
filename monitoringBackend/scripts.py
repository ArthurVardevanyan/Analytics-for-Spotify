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
    userObject = models.Users.objects.get(
        user=str(user))
    listeningHistory = list(models.ListeningHistory.objects.filter(
        user=userObject).values(
            'songID', 'timestamp').order_by('timestamp'))
    listeningHistoryLatest = {}
    for lh in listeningHistory:
        listeningHistoryLatest[lh['songID']] = lh['timestamp']
    playCount = list(models.PlayCount.objects.filter(user=userObject).select_related().values(
        'songID', 'songID__name', 'playCount'))
    history = []
    for play in playCount:
        timestamp = listeningHistoryLatest.get(play['songID'], None)
        if timestamp:
            history.append((
                timestamp,
                play['songID'],
                play['songID__name'],
                play['playCount']
            ))
    logging.info("Total Songs: " + str(len(history)))
    songHistory = []
    for song in history:
        songL = list(song)
        if songL[0] == None:
            songL.pop(0)
            songL.insert(0, 990200212040000)
        songArtist = models.Songs.objects.select_related().filter(
            id=str(song[1])).values('id', 'artists__id', 'artists__name')
        artists = ''
        for artist in songArtist:
            artists += artist['artists__name'] + ","
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
