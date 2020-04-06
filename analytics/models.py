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


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        'DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


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
