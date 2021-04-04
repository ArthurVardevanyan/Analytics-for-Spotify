# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Artists(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'artists'


class Listeninghistory(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='user')
    timestamp = models.BigIntegerField(primary_key=True)
    timeplayed = models.TextField(db_column='timePlayed')  # Field name made lowercase.
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')  # Field name made lowercase.
    json = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'listeningHistory'
        unique_together = (('timestamp', 'user'),)


class Playcount(models.Model):
    user = models.OneToOneField('Users', models.DO_NOTHING, db_column='user', primary_key=True)
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')  # Field name made lowercase.
    playcount = models.IntegerField(db_column='playCount')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'playcount'
        unique_together = (('user', 'songid'),)


class Playlistsongs(models.Model):
    playlistid = models.OneToOneField('Playlists', models.DO_NOTHING, db_column='playlistID', primary_key=True)  # Field name made lowercase.
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')  # Field name made lowercase.
    songstatus = models.TextField(db_column='songStatus')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'playlistSongs'
        unique_together = (('playlistid', 'songid'),)


class Playlists(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='user')
    id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    lastupdated = models.TextField(db_column='lastUpdated')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'playlists'
        unique_together = (('id', 'user'),)


class Songartists(models.Model):
    songid = models.OneToOneField('Songs', models.DO_NOTHING, db_column='songID', primary_key=True)  # Field name made lowercase.
    artistid = models.ForeignKey(Artists, models.DO_NOTHING, db_column='artistID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'songArtists'
        unique_together = (('songid', 'artistid'),)


class Songs(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.TextField()
    tracklength = models.BigIntegerField(db_column='trackLength')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'songs'


class Spotifyapi(models.Model):
    api = models.TextField()

    class Meta:
        managed = False
        db_table = 'spotifyAPI'


class Users(models.Model):
    user = models.CharField(primary_key=True, max_length=128)
    enabled = models.IntegerField()
    statussong = models.IntegerField(db_column='statusSong')  # Field name made lowercase.
    statusplaylist = models.IntegerField(db_column='statusPlaylist')  # Field name made lowercase.
    cache = models.TextField()
    realtime = models.IntegerField(db_column='realTime')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'users'
