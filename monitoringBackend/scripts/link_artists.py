import os
import sys
import django
import logging
import requests
import time

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AnalyticsForSpotify.settings")
django.setup()

import webBackend.models as models
from webBackend.credentials import refresh_token as authorize

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


def get_track_info(access_token: str, track_id: str):
    """
    Get track information from Spotify API

    Parameters:
        access_token (str): Spotify API access token
        track_id (str): Spotify track ID

    Returns:
        dict: Track information or None if failed

    Raises:
        SystemExit: If rate limited (429 error)
    """
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    header = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=header, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            log.error(f"Unauthorized access for track {track_id}")
            return None
        elif response.status_code == 429:
            # Rate limited - exit immediately
            retry_after = response.headers.get('retry-after', 'unknown')
            if retry_after.isdigit():
                retry_seconds = int(retry_after)
                retry_hours = retry_seconds / 3600
                log.error(f"Rate limited (429) for track {track_id}.")
                log.error(f"Retry after: {retry_seconds} seconds ({retry_hours:.2f} hours)")
            else:
                log.error(f"Rate limited (429) for track {track_id}. Retry after: {retry_after}")

            log.error(f"Response headers: {dict(response.headers)}")
            try:
                log.error(f"Response body: {response.json()}")
            except:
                log.error(f"Response text: {response.text}")
            raise SystemExit(1)
        else:
            log.error(f"Failed to get track info for {track_id}: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log.error(f"Exception getting track info for {track_id}: {e}")
        return None


def link_missing_artists():
    """
    Find songs without artist relationships and link them using Spotify API

    Returns:
        dict: Results with counts of successful and failed links
    """
    log.info("Starting scan for songs missing artists")

    # Find songs without any artist relationships
    # Use raw SQL to find songs not in the many-to-many table
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.id
            FROM songs s
            LEFT JOIN songs_artists sa ON s.id = sa.songs_id
            WHERE sa.songs_id IS NULL
        """)
        songs_without_artists = [row[0] for row in cursor.fetchall()]

    log.info(f"Found {len(songs_without_artists)} songs missing artist data")

    # Get a valid access token from any enabled user
    enabled_users = models.Users.objects.filter(enabled=True)
    if not enabled_users.exists():
        log.error("No enabled users found, cannot proceed")
        return {
            'success': False,
            'error': 'No enabled users found',
            'successful_links': 0,
            'failed_links': 0
        }

    # Use first enabled user's token
    user = enabled_users.first()
    access_token = authorize(user.user)

    # Process each song
    successful_links = 0
    failed_links = 0

    for song_id in songs_without_artists:
        try:
            # Fetch track info from Spotify API
            track_info = get_track_info(access_token, song_id)

            if track_info and 'artists' in track_info:
                song_obj = models.Songs.objects.get(id=song_id)

                # Process each artist
                for artist in track_info['artists']:
                    artist_id = artist.get('id')
                    artist_name = artist.get('name')

                    if artist_id:
                        # Create artist if doesn't exist
                        artist_obj, created = models.Artists.objects.get_or_create(
                            id=artist_id,
                            defaults={'name': artist_name}
                        )

                        # Link artist to song
                        song_obj.artists.add(artist_obj)

                successful_links += 1
                if successful_links % 100 == 0:
                    log.info(f"Progress: {successful_links} songs linked")
            else:
                failed_links += 1
                log.warning(f"Failed to get track info for {song_id}")

            # Sleep 1 second between track API calls to avoid rate limiting
            time.sleep(1)

        except Exception as e:
            failed_links += 1
            log.error(f"Error processing song {song_id}: {e}")

    log.info(f"Completed. Successfully linked: {successful_links}, Failed: {failed_links}")

    return {
        'success': True,
        'successful_links': successful_links,
        'failed_links': failed_links,
        'total_processed': len(songs_without_artists)
    }


def main():
    """
    Main entry point for linking missing artists

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        result = link_missing_artists()

        if result['success']:
            log.info(f"Artist linking completed successfully")
            return 0
        else:
            log.error(f"Artist linking failed: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        log.exception(f"Fatal error in artist linking: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
