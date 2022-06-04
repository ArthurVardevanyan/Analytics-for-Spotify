from django.db import models


class SpotifyAPI(models.Model):
    api = models.TextField()

    class Meta:
        managed = True
        db_table = 'spotifyAPI'


class Workers(models.Model):
    worker = models.IntegerField(primary_key=True)
    lastUpdated = models.BigIntegerField()
    creationTime = models.TextField()
    updatedTime = models.TextField()

    class Meta:
        managed = True
        db_table = 'workers'


class Users(models.Model):
    user = models.CharField(primary_key=True, max_length=128)
    enabled = models.IntegerField()
    statusSong = models.IntegerField(db_column='statusSong')
    statusPlaylist = models.IntegerField(db_column='statusPlaylist')
    cache = models.TextField()
    realtime = models.IntegerField(db_column='realTime')
    worker = models.ForeignKey(
        Workers, models.SET_NULL, db_column='worker', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'users'


class Artists(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.TextField()

    class Meta:
        managed = True
        db_table = 'artists'


class Songs(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.TextField()
    trackLength = models.BigIntegerField(db_column='trackLength')

    class Meta:
        managed = True
        db_table = 'songs'


class SongArtists(models.Model):

    songID = models.OneToOneField(
        'Songs', models.RESTRICT, db_column='songID', primary_key=True)
    artistID = models.ForeignKey(
        Artists, models.RESTRICT, db_column='artistID')

    class Meta:
        managed = True
        db_table = 'songArtists'
        unique_together = (('songID', 'artistID'),)


class PlayCount(models.Model):
    user = models.ForeignKey(
        'Users', models.RESTRICT, db_column='user')
    songID = models.ForeignKey('Songs', models.RESTRICT, db_column='songID')
    playCount = models.IntegerField(db_column='playCount', default=1)

    class Meta:
        managed = True
        db_table = 'playCount'
        unique_together = (('user', 'songID'),)


class ListeningHistory(models.Model):
    user = models.ForeignKey('Users', models.RESTRICT, db_column='user')
    songID = models.ForeignKey('Songs', models.RESTRICT, db_column='songID')
    timestamp = models.BigIntegerField()
    timePlayed = models.TextField(db_column='timePlayed')

    class Meta:
        managed = True
        db_table = 'listeningHistory'
        unique_together = (('timestamp', 'user'),)


class Playlists(models.Model):
    playlistID = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=128)
    lastUpdated = models.TextField(db_column='lastUpdated')

    class Meta:
        managed = True
        db_table = 'playlists'


class PlaylistsUsers(models.Model):
    user = models.ForeignKey('Users', models.RESTRICT, db_column='user')
    playlistID = models.ForeignKey(
        'Playlists', models.RESTRICT, to_field='playlistID', db_column='playlistID')

    class Meta:
        managed = True
        db_table = 'playlistsUsers'
        unique_together = (('playlistID', 'user'),)


class PlaylistSongs(models.Model):

    songStatus = models.TextField(db_column='songStatus')
    playlistID = models.ForeignKey(
        'Playlists', models.RESTRICT, to_field='playlistID', db_column='playlistID')
    songID = models.ForeignKey('Songs', models.RESTRICT, db_column='songID')

    class Meta:
        managed = True
        db_table = 'playlistSongs'
        unique_together = (('playlistID', 'songID'),)
