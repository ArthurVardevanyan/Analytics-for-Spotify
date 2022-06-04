# Generated by Django 4.0.5 on 2022-06-04 15:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Artists',
            fields=[
                ('id', models.CharField(max_length=22, primary_key=True, serialize=False)),
                ('name', models.TextField()),
            ],
            options={
                'db_table': 'artists',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Playlists',
            fields=[
                ('playlistID', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('lastUpdated', models.TextField(db_column='lastUpdated')),
            ],
            options={
                'db_table': 'playlists',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Songs',
            fields=[
                ('id', models.CharField(max_length=22, primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('trackLength', models.BigIntegerField(db_column='trackLength')),
            ],
            options={
                'db_table': 'songs',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='SpotifyAPI',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api', models.TextField()),
            ],
            options={
                'db_table': 'spotifyAPI',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Workers',
            fields=[
                ('worker', models.IntegerField(primary_key=True, serialize=False)),
                ('lastUpdated', models.BigIntegerField()),
                ('creationTime', models.TextField()),
                ('updatedTime', models.TextField()),
            ],
            options={
                'db_table': 'workers',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('user', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('enabled', models.IntegerField()),
                ('statusSong', models.IntegerField(db_column='statusSong')),
                ('statusPlaylist', models.IntegerField(db_column='statusPlaylist')),
                ('cache', models.TextField()),
                ('realtime', models.IntegerField(db_column='realTime')),
                ('worker', models.ForeignKey(blank=True, db_column='worker', null=True, on_delete=django.db.models.deletion.SET_NULL, to='webBackend.workers')),
            ],
            options={
                'db_table': 'users',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='PlaylistsUsers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlistID', models.ForeignKey(db_column='playlistID', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.playlists')),
                ('user', models.ForeignKey(db_column='user', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.users')),
            ],
            options={
                'db_table': 'playlistsUsers',
                'managed': True,
                'unique_together': {('playlistID', 'user')},
            },
        ),
        migrations.CreateModel(
            name='PlaylistSongs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('songStatus', models.TextField(db_column='songStatus')),
                ('playlistID', models.ForeignKey(db_column='playlistID', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.playlists')),
                ('songID', models.ForeignKey(db_column='songID', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.songs')),
            ],
            options={
                'db_table': 'playlistSongs',
                'managed': True,
                'unique_together': {('playlistID', 'songID')},
            },
        ),
        migrations.CreateModel(
            name='PlayCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playCount', models.IntegerField(db_column='playCount', default=1)),
                ('songID', models.ForeignKey(db_column='songID', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.songs')),
                ('user', models.ForeignKey(db_column='user', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.users')),
            ],
            options={
                'db_table': 'playCount',
                'managed': True,
                'unique_together': {('user', 'songID')},
            },
        ),
        migrations.CreateModel(
            name='ListeningHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.BigIntegerField()),
                ('timePlayed', models.TextField(db_column='timePlayed')),
                ('songID', models.ForeignKey(db_column='songID', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.songs')),
                ('user', models.ForeignKey(db_column='user', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.users')),
            ],
            options={
                'db_table': 'listeningHistory',
                'managed': True,
                'unique_together': {('timestamp', 'user')},
            },
        ),
        migrations.CreateModel(
            name='SongArtists',
            fields=[
                ('songID', models.OneToOneField(db_column='songID', on_delete=django.db.models.deletion.RESTRICT, primary_key=True, serialize=False, to='webBackend.songs')),
                ('artistID', models.ForeignKey(db_column='artistID', on_delete=django.db.models.deletion.RESTRICT, to='webBackend.artists')),
            ],
            options={
                'db_table': 'songArtists',
                'managed': True,
                'unique_together': {('songID', 'artistID')},
            },
        ),
    ]
