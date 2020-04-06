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
    timestamp = models.BigIntegerField(primary_key=True)
    # Field name made lowercase.
    timeplayed = models.TextField(db_column='timePlayed')
    # Field name made lowercase.
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')
    # This field type is a guess.
    json = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'listeningHistory'


class Playlistsongs(models.Model):
    # Field name made lowercase.
    playlistid = models.ForeignKey(
        'Playlists', models.DO_NOTHING, db_column='playlistID')
    # Field name made lowercase.
    songid = models.OneToOneField(
        'Songs', models.DO_NOTHING, db_column='songID')
    # Field name made lowercase.
    songstatus = models.TextField(db_column='songStatus')

    class Meta:
        managed = False
        db_table = 'playlistSongs'


class Playlists(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.TextField()
    # Field name made lowercase.
    lastupdated = models.TextField(db_column='lastUpdated')

    class Meta:
        managed = False
        db_table = 'playlists'


class Songartists(models.Model):
    # Field name made lowercase.
    songid = models.OneToOneField(
        'Songs', models.DO_NOTHING, db_column='songID', primary_key=True)
    # Field name made lowercase.
    artistid = models.ForeignKey(
        Artists, models.DO_NOTHING, db_column='artistID')

    class Meta:
        managed = False
        db_table = 'songArtists'
        unique_together = (('songid', 'artistid'),)


class Songs(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.TextField()
    # Field name made lowercase.
    playcount = models.IntegerField(
        db_column='playCount', blank=True, null=True)
    # Field name made lowercase.
    tracklength = models.BigIntegerField(db_column='trackLength')

    class Meta:
        managed = False
        db_table = 'songs'

