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
    # Field name made lowercase.
    timeplayed = models.TextField(db_column='timePlayed')
    # Field name made lowercase.
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')
    # This field type is a guess.
    json = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'listeningHistory'
        unique_together = (('timestamp', 'user'),)


class Playcount(models.Model):
    user = models.OneToOneField(
        'Users', models.DO_NOTHING, db_column='user', primary_key=True)
    # Field name made lowercase.
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')
    # Field name made lowercase.
    playcount = models.IntegerField(db_column='playCount')

    class Meta:
        managed = False
        db_table = 'playcount'
        unique_together = (('user', 'songid'),)


class Playlistsongs(models.Model):
    # Field name made lowercase.
    playlistid = models.OneToOneField(
        'Playlists', models.DO_NOTHING, db_column='playlistID', primary_key=True)
    # Field name made lowercase.
    songid = models.ForeignKey('Songs', models.DO_NOTHING, db_column='songID')
    # Field name made lowercase.
    songstatus = models.TextField(db_column='songStatus')

    class Meta:
        managed = False
        db_table = 'playlistSongs'
        unique_together = (('playlistid', 'songid'),)


class Playlists(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='user')
    id = models.CharField(primary_key=True, max_length=128)
    name = models.TextField()
    # Field name made lowercase.
    lastupdated = models.TextField(db_column='lastUpdated')
    # Field name made lowercase.
    idencrypt = models.TextField(db_column='idEncrypt')

    class Meta:
        managed = False
        db_table = 'playlists'
        unique_together = (('id', 'user'),)


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
    tracklength = models.BigIntegerField(db_column='trackLength')

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
    # Field name made lowercase.
    statussong = models.IntegerField(db_column='statusSong')
    # Field name made lowercase.
    statusplaylist = models.IntegerField(db_column='statusPlaylist')
    cache = models.TextField()
    # Field name made lowercase.
    realtime = models.IntegerField(db_column='realTime')

    class Meta:
        managed = False
        db_table = 'users'
