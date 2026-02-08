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
    log.info(f"Starting historical data analysis for user {user_id}")

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
    # Also track ALL exact timestamps (DB has unique constraint on timestamp+user, not timestamp+user+song)
    existing_exact_timestamps = set()
    for song_id, timestamp_str in existing_history:
        # Convert timestamp string (20260207020317) to epoch
        # IMPORTANT: Timestamps are stored as UTC, must specify timezone
        try:
            dt = datetime.strptime(str(timestamp_str), '%Y%m%d%H%M%S')
            # Replace with UTC timezone to match import data
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
            epoch = int(dt.timestamp())
            existing_songs_timestamps[song_id].append(epoch)
            # Track exact timestamp to avoid unique constraint violations
            existing_exact_timestamps.add(int(timestamp_str))
        except (ValueError, AttributeError):
            # Skip invalid timestamps
            continue

    # Debug: Log how many existing entries we loaded
    total_existing = sum(len(timestamps) for timestamps in existing_songs_timestamps.values())
    print(f"DEBUG: Loaded {total_existing} existing listening history entries for {len(existing_songs_timestamps)} unique songs")

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

                                # Convert timestamp to both formats
                                ts = entry.get('ts')
                                if not ts:
                                    continue

                                # Parse as UTC (the 'Z' suffix means UTC)
                                from datetime import timezone
                                dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
                                dt = dt.replace(tzinfo=timezone.utc)
                                epoch_timestamp = int(dt.timestamp())
                                # Format for database: timestamp as YYYYMMDDHHmmss, timePlayed as YYYY-MM-DD HH:MM:SS
                                timestamp_db = int(dt.strftime('%Y%m%d%H%M%S'))
                                timeplayed_db = dt.strftime('%Y-%m-%d %H:%M:%S')

                                # Get track ID
                                track_uri = entry.get('spotify_track_uri', '')
                                track_id = track_uri.replace('spotify:track:', '') if track_uri else None

                                if not track_id:
                                    continue

                                # Check for duplicates
                                # First check: exact timestamp duplicate (DB unique constraint on timestamp+user)
                                if timestamp_db in existing_exact_timestamps:
                                    stats['already_exists'] += 1
                                    continue

                                # Second check: 5-minute sliding window for same song
                                # Use a fixed 5-minute (300 second) window to detect duplicate entries
                                # This accounts for timestamp variations between runtime and historical data
                                is_duplicate = False
                                if track_id in existing_songs_timestamps:
                                    for existing_timestamp in existing_songs_timestamps[track_id]:
                                        time_diff = abs(epoch_timestamp - existing_timestamp)
                                        # 5-minute window catches duplicates from same play event
                                        if time_diff <= 300:
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
                                        'timestamp': timestamp_db,
                                        'time_played': timeplayed_db,
                                        'ms_played': ms_played
                                    })
                                    # Track this timestamp so we don't count duplicates within the same import
                                    existing_songs_timestamps[track_id].append(epoch_timestamp)
                                    existing_exact_timestamps.add(timestamp_db)

                        except json.JSONDecodeError:
                            log.error(f"[{user_id}] Failed to parse JSON file: {filename}")
                            continue

    log.info(f"Analysis complete for user {user_id}: {stats['to_add']} songs to import, {stats['already_exists']} duplicates skipped")
    return stats


def import_historical_data(songs_data, user_id, access_token):
    """
    Actually import the historical data into the database.
    Commits to DB every 1000 songs for resumability.

    Parameters:
        songs_data (list): List of song data dictionaries
        user_id (str): Spotify user ID
        access_token (str): Spotify API access token for looking up track info

    Returns:
        dict: Import results
    """
    log.info(f"Starting historical data import for user {user_id} - {len(songs_data)} songs to process")

    user_obj = models.Users.objects.get(user=str(user_id))

    BATCH_SIZE = 1000

    # Track totals across all batches
    total_artists_created = 0
    total_songs_created = 0
    total_history_entries = 0
    total_duplicates_skipped = 0

    # Get existing songs and artists from DB (will refresh after each batch)
    existing_song_ids = set(models.Songs.objects.values_list('id', flat=True))
    existing_artist_ids = set(models.Artists.objects.values_list('id', flat=True))

    # Load ALL existing listening history into memory for duplicate detection
    # Store as dict[song_id] -> list[epoch_timestamps]
    existing_songs_timestamps = defaultdict(list)
    # Also track ALL exact timestamps (DB has unique constraint on timestamp+user, not timestamp+user+song)
    existing_exact_timestamps = set()
    existing_history = models.ListeningHistory.objects.filter(
        user=user_obj
    ).values('songID_id', 'timestamp')

    for entry in existing_history:
        song_id = entry['songID_id']
        timestamp_str = entry['timestamp']

        try:
            # Convert YYYYMMDDHHmmss to epoch for comparison
            dt = datetime.strptime(str(timestamp_str), '%Y%m%d%H%M%S')
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
            epoch = int(dt.timestamp())
            existing_songs_timestamps[song_id].append(epoch)
            # Track exact timestamp (in original format) to avoid unique constraint violations
            existing_exact_timestamps.add(int(timestamp_str))
        except (ValueError, AttributeError):
            # Skip invalid timestamps
            continue

    log.info(f"[{user_id}] Loaded {len(existing_songs_timestamps)} songs with existing listening history for duplicate detection")

    # Cache track info to avoid duplicate API calls
    track_info_cache = {}

    for batch_start in range(0, len(songs_data), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(songs_data))
        batch = songs_data[batch_start:batch_end]

        log.info(f"[{user_id}] Processing batch {batch_start//BATCH_SIZE + 1} (songs {batch_start + 1}-{batch_end} of {len(songs_data)})")

        # Batch-specific collections
        songs_to_create = []
        artists_to_create = []
        listening_history_to_create = []
        play_counts = defaultdict(int)

        # Track what we've processed in this batch
        processed_songs = set()
        processed_artists = set()

        for i, song_data in enumerate(batch):
            track_id = song_data['track_id']

            # Create new songs using data from import file (no API call needed)
            if track_id not in existing_song_ids and track_id not in processed_songs:
                # Create song object using import data
                songs_to_create.append(models.Songs(
                    id=track_id,
                    name=song_data['track_name'],
                    trackLength=song_data['ms_played']
                ))
                processed_songs.add(track_id)

            # Only add listening history if song exists or was just created
            if track_id in existing_song_ids or track_id in processed_songs:
                # First check: exact timestamp duplicate (DB unique constraint on timestamp+user)
                timestamp_int = int(song_data['timestamp'])
                if timestamp_int in existing_exact_timestamps:
                    total_duplicates_skipped += 1
                    continue  # Skip exact timestamp duplicate

                # Second check: 60-second sliding window for same song
                # Convert timestamp to epoch for comparison
                dt = datetime.strptime(str(song_data['timestamp']), '%Y%m%d%H%M%S')
                dt = dt.replace(tzinfo=timezone.utc)
                epoch_timestamp = int(dt.timestamp())

                is_duplicate = False
                if track_id in existing_songs_timestamps:
                    for existing_timestamp in existing_songs_timestamps[track_id]:
                        time_diff = abs(epoch_timestamp - existing_timestamp)
                        # 5-minute window catches duplicates from same play event
                        if time_diff <= 300:
                            is_duplicate = True
                            total_duplicates_skipped += 1
                            break

                if is_duplicate:
                    continue  # Skip this duplicate

                # Not a duplicate - add to listening history
                # Count plays for this song
                play_counts[track_id] += 1

                # Add to listening history
                listening_history_to_create.append(models.ListeningHistory(
                    user=user_obj,
                    songID_id=track_id,
                    timestamp=song_data['timestamp'],
                    timePlayed=song_data['time_played']
                ))

                # Add this timestamp to our tracking so we don't import duplicates within the same batch
                existing_songs_timestamps[track_id].append(epoch_timestamp)
                existing_exact_timestamps.add(timestamp_int)
            else:
                log.warning(f"[{user_id}] Skipping listening history for non-existent song {track_id}")

        # Commit this batch to database
        try:
            if artists_to_create:
                models.Artists.objects.bulk_create(artists_to_create, ignore_conflicts=True)
                total_artists_created += len(artists_to_create)
                log.info(f"[{user_id}] Batch: Created {len(artists_to_create)} new artists")

            if songs_to_create:
                models.Songs.objects.bulk_create(songs_to_create, ignore_conflicts=True)
                total_songs_created += len(songs_to_create)
                log.info(f"[{user_id}] Batch: Created {len(songs_to_create)} new songs")

                # Refresh existing_song_ids to include songs we just created
                # (in case ignore_conflicts skipped some, we need to know which songs actually exist)
                existing_song_ids = set(models.Songs.objects.values_list('id', flat=True))

                # Link artists to songs using cached track info
                for song in songs_to_create:
                    try:
                        track_info = track_info_cache.get(song.id)
                        if track_info:
                            song_obj = models.Songs.objects.get(id=song.id)
                            for artist in track_info.get('artists', []):
                                try:
                                    artist_obj = models.Artists.objects.get(id=artist['id'])
                                    song_obj.artists.add(artist_obj)
                                except models.Artists.DoesNotExist:
                                    log.error(f"[{user_id}] Artist {artist['id']} not found for song {song.id}")
                    except Exception as e:
                        log.error(f"[{user_id}] Failed to link artists for song {song.id}: {e}")

            if listening_history_to_create:
                # Filter to only include listening history for songs that actually exist
                # (in case some songs failed to create due to conflicts or other issues)
                valid_history = [
                    lh for lh in listening_history_to_create
                    if lh.songID_id in existing_song_ids
                ]
                skipped_count = len(listening_history_to_create) - len(valid_history)
                if skipped_count > 0:
                    log.warning(f"[{user_id}] Skipped {skipped_count} listening history entries for non-existent songs")

                # Don't use ignore_conflicts - we already checked for duplicates
                models.ListeningHistory.objects.bulk_create(valid_history, ignore_conflicts=False)
                total_history_entries += len(valid_history)
                log.info(f"[{user_id}] Batch: Created {len(valid_history)} listening history entries")

            # Update play counts for this batch
            play_count_objects = []
            for song_id, count in play_counts.items():
                try:
                    song_obj = models.Songs.objects.get(id=song_id)
                    play_count, created = models.PlayCount.objects.get_or_create(
                        user=user_obj,
                        songID=song_obj,
                        defaults={'playCount': '0'}
                    )
                    play_count.playCount = str(int(play_count.playCount) + count)
                    play_count_objects.append(play_count)
                except models.Songs.DoesNotExist:
                    log.error(f"[{user_id}] Song {song_id} not found in database")
                    continue

            if play_count_objects:
                models.PlayCount.objects.bulk_update(play_count_objects, ['playCount'])
                log.info(f"[{user_id}] Batch: Updated {len(play_count_objects)} play counts")

            # Refresh existing IDs for next batch
            existing_song_ids.update(processed_songs)
            existing_artist_ids.update(processed_artists)

            log.info(f"[{user_id}] Batch {batch_start//BATCH_SIZE + 1} committed successfully")

        except Exception as e:
            log.exception(f"[{user_id}] Error during batch {batch_start//BATCH_SIZE + 1} import")
            return {
                'success': False,
                'error': 'An internal error occurred during historical import. Please try again later.',
                'partial_import': True,
                'processed_songs': batch_start
            }

    log.info(f"[{user_id}] Historical import completed successfully - Total: {total_artists_created} artists, {total_songs_created} songs, {total_history_entries} history entries, {total_duplicates_skipped} duplicates skipped")
    return {
        'success': True,
        'artists_created': total_artists_created,
        'songs_created': total_songs_created,
        'history_entries': total_history_entries,
        'duplicates_skipped': total_duplicates_skipped
    }
