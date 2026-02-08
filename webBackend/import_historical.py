import json
import logging
import zipfile
import tempfile
import os
from datetime import datetime
from collections import defaultdict
import webBackend.models as models
import monitoringBackend.spotify as spotify_api

log = logging.getLogger(__name__)


def analyze_historical_data(zip_file, user_id):
    """
    Analyze historical Spotify data without inserting into database.

    Parameters:
        zip_file: Uploaded zip file object
        user_id (str): Spotify user ID

    Returns:
        dict: Statistics about what will be imported
    """
    stats = {
        'total': 0,
        'to_add': 0,
        'skipped_duration': 0,
        'skipped_flag': 0,
        'skipped_incognito': 0,
        'already_exists': 0,
        'years_breakdown': defaultdict(int),
        'songs_data': []  # Store for later import
    }

    # Get user's existing listening history (song + timestamp) to avoid duplicates
    # We'll check for duplicates using a sliding window approach
    user_obj = models.Users.objects.get(user=str(user_id))

    # Fetch existing history and convert timestamps to epoch for comparison
    existing_history = list(
        models.ListeningHistory.objects.filter(user=user_obj)
        .values_list('songID_id', 'timestamp')
    )

    # Create a dict mapping song_id -> list of epoch timestamps for faster lookup
    existing_songs_timestamps = defaultdict(list)
    for song_id, timestamp_str in existing_history:
        # Convert timestamp string (20260207020317) to epoch
        try:
            dt = datetime.strptime(str(timestamp_str), '%Y%m%d%H%M%S')
            epoch = int(dt.timestamp())
            existing_songs_timestamps[song_id].append(epoch)
        except (ValueError, AttributeError):
            # Skip invalid timestamps
            continue

    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract zip file
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Process all JSON files
        for root, dirs, files in os.walk(temp_dir):
            for filename in files:
                if filename.endswith('.json') and 'Audio' in filename:
                    filepath = os.path.join(root, filename)

                    with open(filepath, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)

                            for entry in data:
                                stats['total'] += 1

                                # Skip if skipped flag is true
                                if entry.get('skipped', False):
                                    stats['skipped_flag'] += 1
                                    continue

                                # Skip if incognito mode was true
                                if entry.get('incognito_mode', False):
                                    stats['skipped_incognito'] += 1
                                    continue

                                # Skip if less than 30 seconds (30000 ms)
                                ms_played = entry.get('ms_played', 0)
                                if ms_played < 30000:
                                    stats['skipped_duration'] += 1
                                    continue

                                # Convert timestamp to epoch
                                ts = entry.get('ts')
                                if not ts:
                                    continue

                                dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
                                epoch_timestamp = int(dt.timestamp())

                                # Get track ID
                                track_uri = entry.get('spotify_track_uri', '')
                                track_id = track_uri.replace('spotify:track:', '') if track_uri else None

                                if not track_id:
                                    continue

                                # Check if already exists in database using sliding window
                                # Use the song's duration as the window (convert ms to seconds)
                                song_duration_seconds = ms_played / 1000
                                is_duplicate = False
                                if track_id in existing_songs_timestamps:
                                    for existing_timestamp in existing_songs_timestamps[track_id]:
                                        time_diff = abs(epoch_timestamp - existing_timestamp)
                                        # Allow for the full song length plus a small buffer (30 seconds)
                                        if time_diff <= (song_duration_seconds + 30):
                                            is_duplicate = True
                                            break

                                if is_duplicate:
                                    stats['already_exists'] += 1
                                    continue

                                # Valid song to import
                                stats['to_add'] += 1
                                
                                # Track year breakdown
                                year = dt.year
                                stats['years_breakdown'][year] += 1

                                # Store data for later import
                                if track_id:
                                    stats['songs_data'].append({
                                        'track_id': track_id,
                                        'track_name': entry.get('master_metadata_track_name', ''),
                                        'artist_name': entry.get('master_metadata_album_artist_name', ''),
                                        'album_name': entry.get('master_metadata_album_album_name', ''),
                                        'timestamp': epoch_timestamp,
                                        'time_played': ts,
                                        'ms_played': ms_played
                                    })

                        except json.JSONDecodeError:
                            log.error(f"Failed to parse JSON file: {filename}")
                            continue

    return stats


def import_historical_data(songs_data, user_id, access_token):
    """
    Actually import the historical data into the database.

    Parameters:
        songs_data (list): List of song data dictionaries
        user_id (str): Spotify user ID
        access_token (str): Spotify API access token for looking up track info

    Returns:
        dict: Import results
    """
    user_obj = models.Users.objects.get(user=str(user_id))

    # Batch process for efficiency
    songs_to_create = []
    artists_to_create = []
    listening_history_to_create = []
    play_counts = defaultdict(int)

    # Track unique artists and songs
    processed_songs = set()
    processed_artists = set()

    # Get existing songs and artists from DB
    existing_song_ids = set(models.Songs.objects.values_list('id', flat=True))
    existing_artist_ids = set(models.Artists.objects.values_list('id', flat=True))

    for i, song_data in enumerate(songs_data):
        track_id = song_data['track_id']

        # Fetch full track info from Spotify API if not in DB
        if track_id not in existing_song_ids and track_id not in processed_songs:
            try:
                track_info = spotify_api.get_track_info(access_token, track_id)

                if track_info:
                    # Create song object
                    songs_to_create.append(models.Songs(
                        id=track_id,
                        name=track_info.get('name', song_data['track_name']),
                        trackLength=track_info.get('duration_ms', song_data['ms_played'])
                    ))
                    processed_songs.add(track_id)

                    # Process artists
                    for artist in track_info.get('artists', []):
                        artist_id = artist.get('id')
                        artist_name = artist.get('name')

                        if artist_id and artist_id not in existing_artist_ids and artist_id not in processed_artists:
                            artists_to_create.append(models.Artists(
                                id=artist_id,
                                name=artist_name
                            ))
                            processed_artists.add(artist_id)
                            existing_artist_ids.add(artist_id)

            except Exception as e:
                log.error(f"Failed to fetch track info for {track_id}: {e}")
                continue

        # Count plays for this song
        play_counts[track_id] += 1

        # Add to listening history
        listening_history_to_create.append(models.ListeningHistory(
            user=user_obj,
            songID_id=track_id,
            timestamp=song_data['timestamp'],
            timePlayed=song_data['time_played']
        ))

        # Log progress every 100 songs
        if (i + 1) % 100 == 0:
            log.info(f"Processed {i + 1}/{len(songs_data)} songs")

    # Bulk create in database
    try:
        if artists_to_create:
            models.Artists.objects.bulk_create(artists_to_create, ignore_conflicts=True)
            log.info(f"Created {len(artists_to_create)} artists")

        if songs_to_create:
            models.Songs.objects.bulk_create(songs_to_create, ignore_conflicts=True)
            log.info(f"Created {len(songs_to_create)} songs")

            # Link artists to songs
            for song in songs_to_create:
                try:
                    track_info = spotify_api.get_track_info(access_token, song.id)
                    if track_info:
                        song_obj = models.Songs.objects.get(id=song.id)
                        for artist in track_info.get('artists', []):
                            artist_obj = models.Artists.objects.get(id=artist['id'])
                            song_obj.artists.add(artist_obj)
                except Exception as e:
                    log.error(f"Failed to link artists for song {song.id}: {e}")

        if listening_history_to_create:
            models.ListeningHistory.objects.bulk_create(listening_history_to_create, ignore_conflicts=True)
            log.info(f"Created {len(listening_history_to_create)} listening history entries")

        # Update play counts
        play_count_objects = []
        for song_id, count in play_counts.items():
            try:
                song_obj = models.Songs.objects.get(id=song_id)
                play_count, created = models.PlayCount.objects.get_or_create(
                    user=user_obj,
                    songID=song_obj,
                    defaults={'playCount': 0}
                )
                play_count.playCount = str(int(play_count.playCount) + count)
                play_count_objects.append(play_count)
            except models.Songs.DoesNotExist:
                log.error(f"Song {song_id} not found in database")
                continue

        if play_count_objects:
            models.PlayCount.objects.bulk_update(play_count_objects, ['playCount'])
            log.info(f"Updated {len(play_count_objects)} play counts")

        return {
            'success': True,
            'artists_created': len(artists_to_create),
            'songs_created': len(songs_to_create),
            'history_entries': len(listening_history_to_create)
        }

    except Exception as e:
        log.exception("Error during bulk import")
        return {
            'success': False,
            'error': 'An internal error occurred during historical import. Please try again later.'
        }
