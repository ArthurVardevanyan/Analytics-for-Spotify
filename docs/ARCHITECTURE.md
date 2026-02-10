# Architecture Documentation

## System Overview

Analytics for Spotify is a self-hosted listening history tracker built with Django and PostgreSQL, featuring a distributed background worker system for real-time monitoring.

### High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                          User Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  Browser → index.html (public) / analytics.html (authenticated)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Django Backend (views.py)                                       │
│  ├── Authentication (credentials.py)                             │
│  ├── API Endpoints (REST)                                        │
│  └── Historical Import (import_historical.py)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Crunchy Operator)                                   │
│  ├── Users, Songs, Artists, Listening History                    │
│  ├── Play Counts, Playlists                                      │
│  └── Automated Backups (Local + S3)                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Background Worker System                        │
├─────────────────────────────────────────────────────────────────┤
│  Worker Manager (spotify.py)                                     │
│  ├── Playlist Scanner Thread                                     │
│  ├── Listening Monitor Thread (History/Realtime/Hybrid)          │
│  └── Song ID Updater Thread                                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Kubernetes CronJob                              │
├─────────────────────────────────────────────────────────────────┤
│  Artist Linker (link_artists.py)                                 │
│  └── Daily execution at 3 AM                                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                            │
├─────────────────────────────────────────────────────────────────┤
│  Spotify API (OAuth + Data)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Background Worker System

### Worker Lifecycle

#### Initialization

1. Worker boots and calls `database.create_worker()` to register with unique 9-digit ID
2. Queries `scanWorkers()` to get active worker count
3. Calculates initial load: `enabled_users / active_workers`
4. Logs startup info and enters main loop

#### Main Loop (75-second cycle)

```python
while True:
    sleep(75)
    worker_count = database.scanWorkers(WORKER)
    # scanWorkers updates heartbeat, removes stale workers (>90s)
    if worker_count == -1:
        WORKER_HEALTHY = False  # DB connection failed
        continue
    WORKER_HEALTHY = True
    spawnThreads(worker_count)  # Load balancing
```

#### Load Balancing (`spawnThreads`)

**Quota Calculation**:

```python
users_per_worker = ceil(enabled_users / worker_count)
current_threads = len([t for t in THREADS if t[1] == WORKER])
under_quota = current_threads < (users_per_worker * 3)  # 3 threads per user
```

**User Assignment**:

- Query users with `enabled=1` and `worker IS NULL`
- For each unassigned user (up to quota):
  - Set `user.worker = WORKER` in database
  - Spawn 3 threads:
    1. Playlist monitoring
    2. Listening monitoring (history/realtime/hybrid based on `realtime` field)
    3. Song ID updater
  - Wait 5 seconds between users (rate limiting)

**Thread Rebalancing** (`killThreads`):

- Triggered when worker is over quota or user's assigned worker doesn't match
- Sets kill signals in global `KILL` dictionary: `KILL[f"{user}_playlist"] = True`
- Unassigns user: `user.worker = None`
- Threads check `KILL` dict on each iteration and exit gracefully

### Thread Types

#### 1. Playlist Monitor (`playlistThread`)

**Frequency**: Once per day (checks for date change)

**Status Management**:

```python
update_status(user, "statusPlaylist", 1)  # Running
# ... processing ...
update_status(user, "statusPlaylist", 0)  # Stopped
```

**Process**:

1. Fetch user's playlists from `database.playlists_query(user)`
2. For each playlist:
   - Call `playlistSongs.main(user, playlist)`
   - Fetch all songs from Spotify API (paginated, 100 per page)
   - Bulk insert artists, songs, and playlist relationships
3. Sleep 1 hour after completion
4. Check `KILL` dictionary every 360 seconds

#### 2. Listening Monitor (`historySpotify` or `realTimeSpotify`)

**Mode Selection** (via `user.realtime` field):

- `0` = History mode (recently-played endpoint)
- `1` = Realtime mode (currently-playing endpoint)
- `2` = Hybrid mode (both, but only counts local files in realtime)

**History Mode** (`historySpotify`):

- **API**: `/v1/me/player/recently-played?limit=50`
- **Frequency**: Every 20 minutes (1200 seconds)
- **Logic**:

  ```python
  # Fetch last 50 from Spotify
  response = requests.get(url, headers=header).json()
  # Get last 50 from DB
  db_history = ListeningHistory.objects.filter(user=user) \
      .order_by('-timePlayed')[0:50]
  # Compare timestamps, insert only new songs
  for played in response['items']:
      if not in db_history:
          database.database_input(user, played)
  ```

- **Pros**: Low API usage (~3 calls/hour), no delay for offline plays
- **Cons**: 20-minute delay, can miss rapid song changes

**Realtime Mode** (`realTimeSpotify`):

- **API**: `/v1/me/player/currently-playing?market=US`
- **Frequency**: Every 5 seconds
- **Logic**:

  ```python
  response = requests.get(url, headers=header).json()
  if response['is_playing'] and \
     'track' in response['currently_playing_type'] and \
     response['progress_ms'] > 30000:  # 30 seconds
      if response['item']['id'] != previous_track:
          database.database_input(user, response)
          previous_track = response['item']['id']
  ```

- **Pros**: Real-time updates, tracks local files
- **Cons**: High API usage (~720 calls/hour), risk of rate limiting, doesn't work offline

**Hybrid Mode**:

- Runs BOTH history and realtime threads
- Realtime only inserts if `is_local=True`
- History mode handles all non-local plays
- **Use Case**: Users who want local file tracking but prefer history mode otherwise

#### 3. Song ID Updater (`songIdUpdaterThread`)

**Frequency**: Once per day (checks for date change)

**Purpose**: Spotify sometimes changes track IDs for remasters, re-releases, etc.

**Process** (via `songIdUpdater.main()`):

1. Get all play counts with song metadata: `PlayCount.objects.select_related('songID').all()`
2. Group by `(name, artists)` to find duplicates:

   ```python
   song_groups = defaultdict(list)
   for pc in play_counts:
       key = (pc.songID.name, tuple(sorted(artist.name for artist in pc.songID.artists.all())))
       song_groups[key].append(pc)
   ```

3. For each group with multiple IDs:
   - Find newest song (by most recent listening history timestamp)
   - Consolidate play counts to newest ID
   - Update all listening history references
   - Delete old song records
4. Sleep 5000 seconds (~83 minutes) after completion

### 4. Artist Linker CronJob (`link_artists.py`)

**Frequency**: Daily at 3 AM (Kubernetes CronJob)

**Purpose**: Link songs with missing artist relationships (historical imports, API failures, etc.)

**Process**:

1. Query for songs without artist relationships:

   ```sql
   SELECT s.id
   FROM songs s
   LEFT JOIN songs_artists sa ON s.id = sa.songs_id
   WHERE sa.songs_id IS NULL
   AND s.id NOT LIKE ':%'  -- Exclude local files
   ```

2. Get access token from any enabled user via `refresh_token()`
3. For each song without artists:
   - Fetch track metadata from Spotify API `/v1/tracks/{id}`
   - Create artist records if they don't exist
   - Link artists to song via many-to-many relationship
   - Sleep 1 second between API calls (rate limiting)
4. Refresh OAuth token every 45 minutes (proactive refresh before 1-hour expiry)

**Token Management**:

- Tracks `last_token_refresh` timestamp
- Refreshes token every 2700 seconds (45 minutes)
- Prevents 401 errors during long-running jobs (3600+ songs = 1+ hour)

**Rate Limiting**:

- 1 API call per second (3600 calls/hour max)
- Exits immediately on 429 (rate limit) with retry-after header
- Logs progress every 100 songs

**Error Handling**:

- Individual song failures logged but don't stop execution
- Returns summary: `{success, successful_links, failed_links, total_processed}`
- Exit code 0 on success, 1 on fatal error

### Thread Safety & Coordination

**Database as Source of Truth**:

- No shared memory between workers
- All coordination via database fields
- Each worker has unique ID

**Graceful Shutdown**:

```python
# In thread loop:
if KILL.get(f"{user}_{thread_type}"):
    log.info(f"Killing thread {user}_{thread_type}")
    update_status(user, status_field, 0)
    return
```

**Status Fields** (`users` table):

- `enabled`: 0=disabled, 1=enabled (user wants monitoring)
- `statusSong`: 0=stopped, 1=running, 2=processing
- `statusPlaylist`: 0=stopped, 1=running, 2=processing

**Worker Assignment** (`users.worker` FK):

- `NULL` = unassigned (will be picked up by any worker)
- `<worker_id>` = assigned to specific worker
- Updated during load balancing

### Error Handling & Resilience

**Database Errors**:

```python
try:
    worker_count = database.scanWorkers(WORKER)
except Exception:
    WORKER_HEALTHY = False
    log.exception("DB Error")
    continue  # Retry on next cycle
```

**API Errors**:

```python
try:
    response = requests.get(url, headers=header)
    if "access token expired" in response.text.lower():
        header['Authorization'] = f"Bearer {authorize(user)}"  # Refresh token
        response = requests.get(url, headers=header)  # Retry
except requests.exceptions.RequestException:
    log.exception("API Error")
    time.sleep(60)
    continue  # Retry after delay
```

**Rate Limiting** (429 errors):

- History mode: Rarely hits (3 calls/hour)
- Realtime mode: `get_track_info()` exits immediately on 429, logs retry-after
- **Recommended**: Use history mode unless local files are critical

**Worker Failures**:

- Other workers detect stale worker (>90s without heartbeat)
- `scanWorkers()` removes from `workers` table
- Orphaned users (`worker=<dead_id>`) won't match any living worker
- Next cycle, `spawnThreads()` sees them as unassigned (`worker != WORKER`)
- Sets `user.worker = NULL`, making them available for reassignment
- Another worker picks them up within 90 seconds

### Performance Considerations

**Scalability**:

- Horizontal: Add more worker pods, automatic load balancing
- Each user = 3 threads
- Recommendation: ~10-20 users per worker

**API Rate Limits**:

| Mode     | Calls/Hour/User | Risk Level |
| -------- | --------------- | ---------- |
| History  | ~3              | ✅ Safe    |
| Realtime | ~720            | ⚠️ High    |
| Hybrid   | ~723            | ⚠️ High    |

**Database Load**:

- Each user: 3 threads hitting DB on different intervals
- Playlist: Daily + hourly updates
- History: 20-minute polls
- Realtime: 5-second polls (very high)
- Song ID: Daily migration queries

**Optimization Strategies**:

- Use history mode by default
- Batch database operations (playlist scanner uses `bulk_create/bulk_update`)
- Index on `(timestamp, user)` for listening history queries
- Cache OAuth tokens in `users.cache` field

## Data Flow

### Listening Event Flow (History Mode)

```text
User plays song in Spotify
              ↓
    (wait ~20 minutes)
              ↓
Background worker polls /v1/me/player/recently-played
              ↓
   Worker compares with last 50 DB entries
              ↓
New song detected → database.database_input()
              ↓
┌──────────────────────────────────────┐
│ database_input() orchestrates:       │
├──────────────────────────────────────┤
│ 1. add_artists()                     │
│    └─> bulk_create Artists           │
│ 2. add_song()                        │
│    └─> create Song + link Artists    │
│ 3. add_song_count()                  │
│    └─> increment PlayCount           │
│ 4. add_listening_history()           │
│    └─> insert ListeningHistory       │
└──────────────────────────────────────┘
              ↓
  Data available in API immediately
              ↓
Frontend polls /analytics/listeningHistory/
              ↓
  Chart.js renders on analytics.html
```

### Historical Import Flow

```text
 User uploads Spotify data export ZIP
                  ↓
POST /analytics/analyzeHistoricalImport/
                  ↓
┌────────────────────────────────────────┐
│ analyze_historical_data()              │
├────────────────────────────────────────┤
│ 1. Unzip and find JSON files           │
│ 2. Load existing DB timestamps/songs   │
│ 3. Build 3 data structures:            │
│    - existing_songs_timestamps         │
│    - db_by_timebucket (15-min buckets) │
│    - existing_exact_timestamps         │
│ 4. For each entry:                     │
│    ├─ Filter (<30s, incognito, etc.)   │
│    ├─ Exact timestamp check            │
│    ├─ 7.5-min sliding window           │
│    └─ Sequential context check         │
│ 5. Return statistics                   │
└────────────────────────────────────────┘
                  ↓
Display stats to user (songs to import, duplicates, year breakdown)
                  ↓
       User clicks "Import"
                  ↓
POST /analytics/executeHistoricalImport/
                  ↓
┌────────────────────────────────────────┐
│ import_historical_data()               │
├────────────────────────────────────────┤
│ 1. Re-run analysis to get valid songs  │
│ 2. Process in batches of 1000:         │
│    ├─ bulk_create Artists              │
│    ├─ bulk_create Songs                │
│    ├─ Refresh existing_song_ids        │
│    ├─ Filter listening history         │
│    ├─ bulk_create ListeningHistory     │
│    └─ Link artists (individual queries)│
│ 3. Bulk update PlayCounts              │
└────────────────────────────────────────┘
                  ↓
      Data available in API
```

### Duplicate Detection Algorithm

**Phase 1: Exact Timestamp** (O(1))

```python
if timestamp_db in existing_exact_timestamps:
    skip  # DB unique constraint on (timestamp, user)
```

**Phase 2: 7.5-Minute Sliding Window** (O(n) per track)

```python
if track_id in existing_songs_timestamps:
    for existing_epoch in existing_songs_timestamps[track_id]:
        if abs(epoch_timestamp - existing_epoch) <= 450:  # 7.5 min = 450s
            skip  # Same song played within 7.5 minutes
```

**Phase 3: Sequential Context** (O(1) with time-bucketing)

```python
# Get prev/next songs from import data
prev_import_track_id = import_data[i-1]['spotify_track_uri']
next_import_track_id = import_data[i+1]['spotify_track_uri']

# Check if prev/next exist in DB within 15 minutes
current_bucket = epoch_timestamp // 900  # 900s = 15 min
for bucket in [current_bucket-1, current_bucket, current_bucket+1]:
    for db_epoch, db_track_id in db_by_timebucket[bucket]:
        if db_track_id in [prev_import_track_id, next_import_track_id]:
            skip  # Session already captured by runtime monitoring
```

**Why 3 Phases?**

1. **Exact timestamp**: Prevents constraint violations
2. **7.5-minute window**: Handles timestamp drift between runtime and historical data (Spotify's timestamps differ)
3. **Sequential context**: Detects when a listening session was already captured by background monitoring but timestamps don't match

**Performance**:

- Phase 1: O(1) set lookup
- Phase 2: O(n) where n = plays of that specific track (typically <100)
- Phase 3: O(1) time-bucketing (checks ~30-50 entries instead of 131K)
- **Total**: O(n) instead of O(n²) for naive approach

## Authentication & Security

### OAuth Flow

```text
User clicks "Log In"
       ↓
GET /analytics/login/
       ↓
Redirect to Spotify authorization:
https://accounts.spotify.com/authorize
  ?client_id=<CLIENT_ID>
  &response_type=code
  &redirect_uri=<REDIRECT_URL>
  &scope=user-read-currently-playing+user-read-recently-played
       ↓
User approves permissions
       ↓
Spotify redirects to: <REDIRECT_URL>?code=<AUTH_CODE>
       ↓
GET /analytics/loginResponse?code=<AUTH_CODE>
       ↓
POST https://accounts.spotify.com/api/token
  grant_type=authorization_code
  code=<AUTH_CODE>
  redirect_uri=<REDIRECT_URL>
  Authorization: Basic <BASE64(client_id:client_secret)>
       ↓
Receive access_token + refresh_token (expires in 3600s)
       ↓
GET https://api.spotify.com/v1/me
  Authorization: Bearer <access_token>
       ↓
Get user ID → Store in session
       ↓
Store tokens in users.cache (JSON):
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": 1234567890
}
       ↓
Redirect to /spotify/analytics/
```

### Token Refresh (credentials.py)

```python
def refresh_token(userID: str):
    user_data = json.loads(Users.objects.get(user=userID).cache)

    # Check if token expired
    if time.time() >= user_data.get('expires_at', 0):
        # POST to /api/token with grant_type=refresh_token
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers={'Authorization': f"Basic {getAPI()['B64CS']}"},
            data={
                'grant_type': 'refresh_token',
                'refresh_token': user_data['refresh_token']
            }
        )
        new_token = response.json()
        # Update cache with new access_token and expires_at
        user_data['access_token'] = new_token['access_token']
        user_data['expires_at'] = time.time() + new_token['expires_in']
        Users.objects.filter(user=userID).update(cache=json.dumps(user_data))

    return user_data['access_token']
```

**Token Lifecycle**:

- Access token: 3600 seconds (1 hour)
- Refresh token: Never expires (until revoked)
- Background workers call `refresh_token()` before each API request
- Frontend session: 86400 seconds (24 hours)

### Session Management

**Django Sessions**:

- Storage: Database (default)
- Cookie: `sessionid`, HttpOnly, Secure
- Age: 86400 seconds (24 hours)
- CSRF protection: Enabled with trusted origins

**Session Data**:

```python
request.session['spotify'] = user_id  # Spotify user ID
```

**Authentication Check**:

```python
def authenticated(request):
    spotify_id = request.session.get('spotify', False)
    if spotify_id == False:
        return HttpResponse("False", status=401)
    return HttpResponse("True", status=200)
```

## API Integration

### Spotify API Usage

**Endpoints Used**:

| Endpoint                                    | Purpose           | Frequency    | Mode          |
| ------------------------------------------- | ----------------- | ------------ | ------------- |
| `/v1/me`                                    | Get user profile  | Once (login) | All           |
| `/v1/me/player/recently-played?limit=50`    | Listening history | Every 20 min | History       |
| `/v1/me/player/currently-playing?market=US` | Current playback  | Every 5 sec  | Realtime      |
| `/v1/playlists/{id}/tracks`                 | Playlist songs    | Daily        | All           |
| `/v1/tracks/{id}`                           | Track metadata    | On demand    | Artist linker |

**Required Scopes**:

- `user-read-currently-playing`
- `user-read-recently-played`

**Rate Limiting Strategy**:

- History mode: ~3 calls/hour (well under Spotify's limits)
- Realtime mode: ~720 calls/hour (approaching limits for multiple users)
- Artist linker: 1 call/second with 1-second sleep between requests
- Retry logic: Sleep 60s on errors, exit on 429 (rate limit)
- Token refresh: Automatic on 401 errors

**Token Management**:

All background workers and scripts automatically refresh OAuth tokens:

- Access tokens expire after 1 hour (3600 seconds)
- Proactive refresh every 45 minutes (2700 seconds) for long-running processes
- Artist linker CronJob refreshes token mid-run to handle large datasets
- Refresh logic in `credentials.py` updates `users.cache` field with new token

**Local File Handling**:

Spotify's API doesn't provide IDs for local files. Custom ID generation:

```python
# Format: :XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (padded to 22 chars)
local_id = ":" + song_uri.replace("%2C", "").replace("+", "") \
    .replace("%28", "").replace(":", "")[12:30] + song_uri[-3:]
local_id = local_id[:22]

# Artist ID:
artist_id = (":" + artist_name).zfill(22)[:22]
```

This ensures:

- Starts with `:` to distinguish from real Spotify IDs
- Deterministic (same local file = same ID)
- Fits in `CharField(22)` database field

## Frontend & User Interface

### Theme System

**Auto-Detection with Manual Override**:

The application features a comprehensive dark/light theme system with automatic detection and manual controls.

**Theme Modes**:

- **Light Mode** (☀): Force light theme regardless of system preferences
- **Dark Mode** (☾): Force dark theme regardless of system preferences
- **Auto Mode** (◐): Automatically follows system `prefers-color-scheme` setting

**Implementation** (`theme.js`):

```javascript
// Detects system preference
const systemPrefersDark = window.matchMedia(
  "(prefers-color-scheme: dark)",
).matches;

// Persists user choice in localStorage
localStorage.setItem("theme-preference", "auto|light|dark");

// Applies theme by setting data attribute
document.documentElement.setAttribute("data-theme", "light|dark");
```

**CSS Variables** (`main.css`):

All colors use CSS custom properties that adapt to the active theme:

```css
:root {
  --bg-primary: #ffffff;
  --text-primary: #000000;
  --btn-bg: #f0f0f0;
  /* ... */
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --text-primary: #e0e0e0;
  --btn-bg: #555;
  /* ... */
}
```

**Features**:

- **Real-time switching**: Theme changes apply instantly without page reload
- **Chart.js integration**: Automatically updates chart colors when theme changes
- **Persistent preference**: User's choice saved in localStorage across sessions
- **System sync**: In Auto mode, listens for system theme changes via `matchMedia` API
- **Smooth transitions**: CSS transitions on theme changes (0.3s ease)

**Theme Toggle UI**:

- Located in top button bar alongside Settings
- Cycles through: Light → Dark → Auto
- Visual indicator shows current mode with icon
- Hover tooltip displays active theme (e.g., "Auto (dark)")

### Settings Menu

**Dropdown Interface**:

The Settings button reveals a dropdown menu with user account controls:

- **Delete User**: Removes account and all listening history (confirmation required)
- **Stop Service**: Pauses monitoring with confirmation ("This will pause tracking your listening history")
- **Start Service**: Resumes background monitoring
- **Log Out**: Clears session and redirects to homepage

**Implementation**:

- JavaScript-controlled visibility (`toggleOptions()` function)
- Click-outside-to-close behavior
- Positioned absolutely relative to button
- Theme-aware styling with CSS variables

### Color Coding

**Interactive Elements**:

- **Green text**: Start Service, Log Out buttons (Spotify brand color #1db954)
- **Red text**: Delete User, Stop Service buttons (destructive actions #E10000)
- **Default buttons**: White text (light mode) / Black text (dark mode)
- **Hover states**: Brighter versions of base colors (#1ed760 for green, #ff4444 for red)

**Status Indicators**:

- **Service Running**: Green (#1DB954)
- **Service Stopping**: Gold (#FFD700)
- **Service Not Running**: Red (#FF4444)

## CI/CD Pipeline

### Overview

The project uses Tekton Pipelines for continuous integration and deployment on Kubernetes/OpenShift.

### Pipeline Triggers

**GitHub Webhook Integration**:

- EventListener exposed via OpenShift Route
- Listens for git push events to any branch
- Triggers PipelineRun with git metadata (commit SHA, branch ref, repository URL)

**Trigger Binding** (`binding.yaml`):

- Extracts parameters from GitHub webhook payload
- Maps to pipeline parameters: `git-url`, `git-name`, `git-commit`, `git-ref`

### Main Pipeline (`pipeline.yaml`)

**Execution Flow**:

```text
   GitHub Push Event
            ↓
EventListener (webhook)
            ↓
TriggerTemplate creates PipelineRun
            ↓
┌──────────────────────────────┐
│ 1. git-pending               │ ← Set GitHub status to "pending"
└──────────────────────────────┘
            ↓
┌──────────────────────────────┐
│ 2. git-clone                 │ ← Clone repository at commit SHA
└──────────────────────────────┘
            ↓
┌────────────────┬─────────────┐
│ 3a. unit-test  │ 3b. build-  │ ← Parallel execution
│                │     image   │
└────────────────┴─────────────┘
            ↓
┌──────────────────────────────┐
│ 4. deploy                    │ ← Update Kustomize overlay with new image SHA
└──────────────────────────────┘
            ↓
┌──────────────────────────────┐
│ finally: git-success/failure │ ← Set GitHub commit status
└──────────────────────────────┘
```

### Pipeline Tasks

#### 1. GitHub Status (git-pending)

**Purpose**: Update GitHub commit status to "pending"

**Conditions**: Only runs for `production` branch (refs/heads/production)

**Task**: `github-set-status` (ClusterTask)

**Parameters**:

- STATE: `pending`
- DESCRIPTION: "Pipeline Running"
- CONTEXT: "Tekton CI/CD"

#### 2. Git Clone

**Purpose**: Clone repository at specific commit SHA

**Task**: `git-clone` (ClusterTask from Tekton Catalog)

**Workspace**: Clones to `data` workspace (250Mi PVC)

#### 3a. Unit Tests (parallel)

**Purpose**: Run Django unit tests with PostgreSQL sidecar

**Task**: `unit-test` (custom task in `unit-test.yaml`)

**Sidecar Container**:

- PostgreSQL 17.4 (docker.io/library/postgres)
- Database: `spotify`, User: `spotify`, Password: `spotify`
- Resources: 192Mi-384Mi memory, 100m-300m CPU
- Security: Non-root (65532), read-only FS, drop all capabilities

**Test Steps**:

1. Wait for database to start
2. Install dependencies: `pip install -r requirements.txt`
3. Create virtual environment and reinstall (for isolation)
4. Run tests with coverage: `coverage run --source='./monitoringBackend,./webBackend' manage.py test`
5. Generate coverage report: `coverage report -m`
6. Retry up to 5 times with exponential backoff (60s base delay)

**Security Context**:

- Non-root execution (UID 65532)
- Read-only root filesystem
- Drop all capabilities
- No privilege escalation

#### 3b. Build Image (parallel)

**Purpose**: Build container image using Buildah

**Task**: `buildah` (ClusterTask from Tekton Catalog)

**Parameters**:

- IMAGE: `registry.arthurvardevanyan.com/apps/analytics-for-spotify:<commit-sha>`
- DOCKERFILE: `./containerfile`

**Multi-Stage Build Architecture**:

The application uses a multi-stage build with separate base images:

- **base-builder**: Contains build tools (gcc, pkg-config, pip) for compiling Python packages
- **base-runtime**: Contains only runtime dependencies (Apache, mod-wsgi, Python)
- **Final image**: Copies compiled packages from builder → runtime, excludes build tools

Benefits:

- ~85-100MB smaller final images (no gcc, pkg-config, pip in production)
- Better security: Build tools excluded from runtime
- Faster rebuilds: Base images cached independently
- Clean separation: Builder has compilation tools, runtime has only Apache

Base images are built separately via `.tekton/base-image-builder.yaml` and `.tekton/base-image-runtime.yaml` pipelines.

**Build Process**:

- Uses Buildah to build OCI-compliant image
- Multi-stage: Compiles packages in builder, copies to runtime
- Tags with git commit SHA for immutable deployments
- Pushes to private registry (registry.arthurvardevanyan.com)

#### 4. Deploy

**Purpose**: Update Kubernetes manifests with new image SHA

**Conditions**: Only runs for `production` branch

**Task**: `deploy` (ClusterTask)

**Process**:

1. Updates Kustomize overlay with new image reference
2. Commits change to git repository
3. ArgoCD detects manifest change and syncs deployment

**ArgoCD Integration**:

- Auto-sync enabled with prune and self-heal
- Monitors `kubernetes/overlays/okd-external/` path
- Deploys updated image to `analytics-for-spotify` namespace

### Finally Tasks

**git-success** (runs if pipeline succeeds):

- Sets GitHub commit status to "success"
- DESCRIPTION: "Completed Successfully"

**git-failure** (runs if any task fails):

- Sets GitHub commit status to "error"
- DESCRIPTION: "Pipeline Failed"

### Pipeline Resources

**Workspace**:

- Name: `data`
- Type: VolumeClaimTemplate (dynamically provisioned)
- Size: 250Mi
- StorageClass: `longhorn` (distributed block storage)
- AccessMode: ReadWriteMany (shared across tasks)

**Execution Limits**:

- Timeout: 15 minutes (entire pipeline)
- Service Account: `pipeline` (with RBAC for registry push and git commits)

**Persistent Cache**:

- PVC `cache` for pip packages (speeds up dependency installation)
- Mounted at `/.cache/` and `/.local/` in test container

### Image Build Pipeline (`image-build-pipeline.yaml`)

**Purpose**: Build base images (separate from main pipeline)

**Tasks**:

1. git-clone
2. buildah (build base image)

**Use Case**: Build base image with Python dependencies for faster CI runs

### Security

**RBAC** (`rbac.yaml`):

- ServiceAccount: `pipeline`
- Permissions: Create/update PipelineRuns, PVCs, and Pods
- Secret access: Registry credentials, GitHub token

**Network Policy** (`network-policy.yaml`):

- Allow egress to GitHub for git clone
- Allow egress to container registry
- Allow egress to Kubernetes API
- Deny all other traffic

**Secret Management**:

- Registry credentials: `push-secret` (for image push)
- GitHub token: For commit status updates

### Monitoring

**PipelineRun Status**:

- View in OpenShift Console: Pipelines → PipelineRuns
- CLI: `tkn pipelinerun logs <name> -f -n analytics-for-spotify-ci`

**GitHub Integration**:

- Commit statuses visible in GitHub UI
- Pull request checks automatically updated
- Required status checks enforced before merge

### Branch Strategy

**Production Branch**:

- Triggers full pipeline (test → build → deploy)
- Updates GitHub status
- Deploys to production namespace

**Other Branches**:

- Only clones repository (no status updates or deployment)
- Useful for testing pipeline changes
