# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class SpotifyAPI(models.Model):
    api = models.TextField()

    class Meta:
        managed = True
        db_table = 'spotifyAPI'


class Users(models.Model):
    user = models.CharField(primary_key=True, max_length=128)
    enabled = models.IntegerField()
    statussong = models.IntegerField(db_column='statusSong')
    statusplaylist = models.IntegerField(db_column='statusPlaylist')
    cache = models.TextField()
    realtime = models.IntegerField(db_column='realTime')

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
    tracklength = models.BigIntegerField(db_column='trackLength')

    class Meta:
        managed = True
        db_table = 'songs'


class Songartists(models.Model):

    songID = models.OneToOneField(
        'Songs', models.DO_NOTHING, db_column='songID', primary_key=True)
    artistID = models.ForeignKey(
        Artists, models.DO_NOTHING, db_column='artistID')

    class Meta:
        managed = True
        db_table = 'songArtists'
        unique_together = (('songID', 'artistID'),)


class Playcount(models.Model):
    user = models.ForeignKey(
        'Users', models.DO_NOTHING, db_column='user')
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')
    playcount = models.IntegerField(db_column='playCount', default=1)

    class Meta:
        managed = True
        db_table = 'playcount'
        unique_together = (('user', 'songid'),)


class Listeninghistory(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='user')
    timestamp = models.BigIntegerField(primary_key=True)
    timeplayed = models.TextField(db_column='timePlayed')
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')
    json = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'listeningHistory'
        unique_together = (('timestamp', 'user'),)


class Playlists(models.Model):
    playlistID = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=128)
    lastupdated = models.TextField(db_column='lastUpdated')

    class Meta:
        managed = True
        db_table = 'playlists'


class Playlistsusers(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='user')
    playlistID = models.ForeignKey(
        'Playlists', models.DO_NOTHING, to_field='playlistID', db_column='playlistID')

    class Meta:
        managed = True
        db_table = 'playlistsUsers'
        unique_together = (('playlistID', 'user'),)



class Playlistsongs(models.Model):

    songstatus = models.TextField(db_column='songStatus')
    playlistID = models.ForeignKey(
        'Playlists', models.CASCADE, to_field='playlistID', db_column='playlistID')
    songID = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')

    class Meta:
        managed = True
        db_table = 'playlistSongs'
        unique_together = (('playlistID', 'songID'),)
