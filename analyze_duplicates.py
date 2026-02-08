#!/usr/bin/env python3
"""
Analyze streaming history files against database to detect duplicates.
Applies same filtering logic as the import system.
"""

import json
import glob
import csv
from datetime import datetime, timezone
from collections import defaultdict

def main():
    print("Loading database data (listeningHistory_DB.csv)...")

    # Build database timestamp map (track_id -> list of epoch timestamps)
    db_timestamps = defaultdict(list)
    db_exact_timestamps = set()

    with open('secrets/listeningHistory_DB.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_id = row['songID']
            timestamp_str = row['timePlayed']
            timestamp_db_str = row['timestamp']

            if track_id and timestamp_str:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                dt = dt.replace(tzinfo=timezone.utc)
                epoch = int(dt.timestamp())
                db_timestamps[track_id].append(epoch)
                db_exact_timestamps.add(int(timestamp_db_str))

    print(f"Loaded {len(db_exact_timestamps):,} entries from database")
    print(f"Unique tracks: {len(db_timestamps):,}")
    print()

    # Find all audio streaming history files
    import_files = sorted(glob.glob('secrets/Spotify Extended Streaming History/Streaming_History_Audio_*.json'))
    print(f"Found {len(import_files)} streaming history files:")
    for f in import_files:
        print(f"  - {f.split('/')[-1]}")
    print()

    # Statistics
    stats = {
        'total': 0,
        'skipped_flag': 0,
        'skipped_incognito': 0,
        'skipped_duration': 0,
        'no_timestamp': 0,
        'no_track_id': 0,
        'exact_duplicate_timestamp': 0,
        'duplicates_60s': 0,
        'duplicates_7_5min': 0,
        'duplicates_10min': 0,
        'duplicates_6hour': 0,
        'new_entries': 0,
        'years_breakdown': defaultdict(int)
    }

    examples_7_5min = []
    examples_60s = []

    # Track exact timestamps we've seen (to simulate DB unique constraint)
    seen_exact_timestamps = set(db_exact_timestamps)

    for file_path in import_files:
        print(f"Processing {file_path.split('/')[-1]}...")

        with open(file_path, 'r') as f:
            import_data = json.load(f)

        for entry in import_data:
            stats['total'] += 1

            if stats['total'] % 50000 == 0:
                print(f"  Total processed: {stats['total']:,} entries...")

            # Apply same filtering logic as import_historical.py

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

            # Get timestamp
            ts_str = entry.get('ts')
            if not ts_str:
                stats['no_timestamp'] += 1
                continue

            # Get track ID and name
            track_uri = entry.get('spotify_track_uri', '')
            track_id = track_uri.replace('spotify:track:', '') if track_uri else None
            name = entry.get('master_metadata_track_name')

            if not track_id or not name:
                stats['no_track_id'] += 1
                continue

            # Parse timestamp
            dt = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ')
            dt = dt.replace(tzinfo=timezone.utc)
            epoch_timestamp = int(dt.timestamp())
            timestamp_db = int(dt.strftime('%Y%m%d%H%M%S'))

            # First check: exact timestamp duplicate (DB unique constraint)
            if timestamp_db in seen_exact_timestamps:
                stats['exact_duplicate_timestamp'] += 1
                continue

            # Second check: sliding window for same song (by track ID)
            is_duplicate_7_5min = False
            is_duplicate_60s = False
            is_duplicate_10min = False
            is_duplicate_6hour = False
            min_diff = None

            if track_id in db_timestamps:
                for db_epoch in db_timestamps[track_id]:
                    time_diff = abs(epoch_timestamp - db_epoch)
                    if min_diff is None or time_diff < min_diff:
                        min_diff = time_diff

                    if time_diff <= 450:  # 7.5 minutes
                        is_duplicate_7_5min = True
                    if time_diff <= 60:
                        is_duplicate_60s = True
                    if time_diff <= 600:
                        is_duplicate_10min = True
                    if time_diff <= 21600:  # 6 hours
                        is_duplicate_6hour = True

            if is_duplicate_60s:
                stats['duplicates_60s'] += 1
                if len(examples_60s) < 5:
                    examples_60s.append((name, ts_str, min_diff))
            elif is_duplicate_5min:
                stats['duplicates_5min'] += 1
                if len(examples_5min) < 5:
                    examples_5min.append((name, ts_str, min_diff))
            elif is_duplicate_10min:
                stats['duplicates_10min'] += 1
            elif is_duplicate_6hour:
                stats['duplicates_6hour'] += 1
            else:
                stats['new_entries'] += 1
                # Track year breakdown
                stats['years_breakdown'][dt.year] += 1
                # Track this timestamp for exact duplicate detection
                seen_exact_timestamps.add(timestamp_db)

    # Print results
    print(f"\n{'='*70}")
    print(f"ANALYSIS RESULTS FOR ALL {stats['total']:,} ENTRIES:")
    print(f"{'='*70}")
    print()
    print("Filtering (same as import logic):")
    print(f"  Skipped (skipped flag): {stats['skipped_flag']:,}")
    print(f"  Skipped (incognito): {stats['skipped_incognito']:,}")
    print(f"  Skipped (< 30 seconds): {stats['skipped_duration']:,}")
    print(f"  Skipped (no timestamp): {stats['no_timestamp']:,}")
    print(f"  Skipped (no track ID): {stats['no_track_id']:,}")
    print()

    total_filtered = (stats['skipped_flag'] + stats['skipped_incognito'] +
                     stats['skipped_duration'] + stats['no_timestamp'] +
                     stats['no_track_id'])
    valid_entries = stats['total'] - total_filtered

    print(f"Total filtered out: {total_filtered:,}")
    print(f"Valid entries to process: {valid_entries:,}")
    print()

    print("Duplicate Detection:")
    print(f"  Exact duplicate timestamps: {stats['exact_duplicate_timestamp']:,}")
    print(f"  Duplicates within 60s: {stats['duplicates_60s']:,}")
    print(f"  Duplicates within 5min (but >60s): {stats['duplicates_5min']:,}")
    print(f"  Duplicates within 10min (but >5min): {stats['duplicates_10min']:,}")
    print(f"  Duplicates within 6hr (but >10min): {stats['duplicates_6hour']:,}")
    total_dups_5min = stats['exact_duplicate_timestamp'] + stats['duplicates_60s'] + stats['duplicates_5min']
    total_dups_10min = total_dups_5min + stats['duplicates_10min']
    total_dups_6hour = total_dups_10min + stats['duplicates_6hour']
    print(f"  Total duplicates (5min window): {total_dups_5min:,}")
    print(f"  Total duplicates (10min window): {total_dups_10min:,}")
    print(f"  Total duplicates (6hr window): {total_dups_6hour:,}")
    print(f"  New entries to add (5min): {stats['new_entries']:,}")
    print(f"  New entries to add (10min): {stats['new_entries'] - stats['duplicates_10min']:,}")
    print(f"  New entries to add (6hr): {stats['new_entries'] - stats['duplicates_10min'] - stats['duplicates_6hour']:,}")
    print()

    # Print year breakdown
    print("New Entries Breakdown by Year:")
    for year in sorted(stats['years_breakdown'].keys()):
        count = stats['years_breakdown'][year]
        print(f"  {year}: {count:,} entries")
    print()

    if total_dups_5min > 0:
        pct_5min_only = stats['duplicates_5min'] * 100 / total_dups_5min
        print(f"Impact of 5-minute window:")
        print(f"  Caught {stats['duplicates_5min']:,} additional duplicates ({pct_5min_only:.1f}% of total)")
        print(f"  that would have been MISSED with 60s window")
        print()

    if total_dups_10min > 0:
        pct_10min_only = stats['duplicates_10min'] * 100 / total_dups_10min
        print(f"Impact of 10-minute window:")
        print(f"  Would catch {stats['duplicates_10min']:,} additional duplicates ({pct_10min_only:.1f}% of total)")
        print(f"  that are MISSED with 5min window")
        print()

    if total_dups_6hour > 0:
        pct_6hour_only = stats['duplicates_6hour'] * 100 / total_dups_6hour
        print(f"Impact of 6-hour window:")
        print(f"  Would catch {stats['duplicates_6hour']:,} additional duplicates ({pct_6hour_only:.1f}% of total)")
        print(f"  that are MISSED with 10min window")
        print()

    if examples_60s:
        print("Examples caught by 60s window:")
        for name, ts, diff in examples_60s[:5]:
            print(f"  '{name}' - {ts} ({diff}s difference)")
        print()

    if examples_5min:
        print("Examples ONLY caught by 5-minute window:")
        for name, ts, diff in examples_5min[:5]:
            print(f"  '{name}' - {ts} ({diff}s = {diff//60}m {diff%60}s difference)")

if __name__ == "__main__":
    main()
