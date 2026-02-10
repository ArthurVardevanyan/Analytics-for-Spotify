# API Documentation

## Base URL

- **Development**: `http://localhost:8000/analytics`
- **Production**: `https://<your-domain>/analytics`

## Authentication

All authenticated endpoints require an active Django session with Spotify user ID stored.

**Session Cookie**: `sessionid`

**Check Authentication**:

```bash
GET /analytics/authenticated/
```

**Response**:

- `200 OK` + `"True"` if authenticated
- `401 Unauthorized` + `"False"` if not authenticated

## Endpoints

### Authentication & Session Management

#### Login

Redirects to Spotify OAuth authorization page.

```http
GET /analytics/login/
```

**Response**: 302 redirect to Spotify authorization page

---

#### Login Callback

Handles OAuth callback from Spotify with authorization code.

```http
GET /analytics/loginResponse?code={auth_code}
```

**Query Parameters**:

- `code` (required): Authorization code from Spotify

**Response**: 302 redirect to `/spotify/analytics/` (dashboard)

**Side Effects**:

- Creates or updates `Users` record
- Stores access/refresh tokens in `users.cache`
- Sets session: `request.session['spotify'] = user_id`

---

#### Logout

Ends user session.

```http
GET /analytics/logout/
```

**Response**: 302 redirect to `/spotify/`

**Side Effects**: Flushes session data

---

#### Check Authentication

Check if user is authenticated.

```http
GET /analytics/authenticated/
```

**Response**:

- `200 OK` + `"True"` if authenticated
- `401 Unauthorized` + `"False"` if not authenticated

---

### User Controls

#### Start Monitoring

Enable background monitoring for authenticated user.

```http
GET /analytics/start/
```

**Response**: `200 OK` + `"Started"`

**Side Effects**:

- Sets `users.enabled = 1`
- Sets `users.worker = NULL` (makes user available for assignment)

---

#### Stop Monitoring

Disable background monitoring for authenticated user.

```http
GET /analytics/stop/
```

**Response**: `200 OK` + `"Stopped"`

**Side Effects**:

- Sets `users.enabled = 0`
- Background workers will gracefully terminate threads for this user

---

#### Delete User

Delete all user data and end session.

```http
GET /analytics/deleteUser/
```

**Response**: 302 redirect to `/spotify/`

**Side Effects**:

- Deletes all `ListeningHistory` records
- Deletes all `PlayCount` records
- Deletes `Users` record (cascades to `Workers` via FK)
- Flushes session

---

### Health & Status

#### Health Check

Returns app health status.

```http
GET /analytics/health/
```

**Response**:

```json
{
  "status": "healthy"
}
```

---

#### Status Check

Returns detailed database statistics.

```http
GET /analytics/status/
```

**Response**:

```json
{
  "users": 42,
  "artists": 15234,
  "songs": 87654,
  "listening_history": 1234567,
  "play_count": 54321,
  "playlists": 234,
  "workers": 3
}
```

---

### Listening History & Statistics

#### Listening History

Get paginated listening history for authenticated user.

```http
GET /analytics/listeningHistory/?start={start}&length={length}
```

**Query Parameters**:

- `start` (optional, default=0): Offset for pagination
- `length` (optional, default=50): Number of records to return

**Response**:

```json
{
  "data": [
    {
      "timePlayed": "2024-01-15 14:32:45",
      "song": "Song Name",
      "artists": "Artist 1, Artist 2",
      "songID": "7ouMYWpwJ422jRcDASZB7P"
    }
  ]
}
```

**Note**: Returns most recent plays first (ordered by `timePlayed DESC`)

---

#### Song Statistics

Get detailed song statistics with play counts for authenticated user.

```http
GET /analytics/songs/?start={start}&length={length}
```

**Query Parameters**:

- `start` (optional, default=0): Offset for pagination
- `length` (optional, default=50): Number of records to return

**Response**:

```json
{
  "data": [
    {
      "song": "Song Name",
      "artists": "Artist 1, Artist 2",
      "plays": 42,
      "songID": "7ouMYWpwJ422jRcDASZB7P"
    }
  ]
}
```

**Note**: Ordered by play count descending

---

#### Daily Aggregation

Get listening stats aggregated by day for authenticated user.

```http
GET /analytics/dailyAggregation/
```

**Response**:

```json
[
  {
    "date": "2024-01-15",
    "plays": 42,
    "uniqueSongs": 28,
    "uniqueArtists": 15
  }
]
```

**Note**: Returns up to 365 days of data, ordered by date descending

---

#### Hourly Aggregation

Get listening stats aggregated by hour-of-day for authenticated user.

```http
GET /analytics/hourlyAggregation/
```

**Response**:

```json
[
  {
    "hour": 14,
    "plays": 123,
    "avgPlays": 4.2
  }
]
```

**Note**:

- `hour`: 0-23 (24-hour format)
- `avgPlays`: Average plays across all days for this hour

---

#### Personal Stats

Get summary statistics for authenticated user.

```http
GET /analytics/stats/
```

**Response**:

```json
{
  "totalPlays": 12345,
  "uniqueSongs": 2345,
  "uniqueArtists": 567,
  "topSong": {
    "name": "Song Name",
    "artists": "Artist 1, Artist 2",
    "plays": 89
  },
  "topArtist": {
    "name": "Artist Name",
    "plays": 234
  },
  "firstPlay": "2020-01-15 10:23:45",
  "lastPlay": "2024-01-15 18:45:12"
}
```

---

### Playlist Management

#### Submit Playlist

Add or update a playlist for monitoring.

```http
POST /analytics/playlistSubmission/
Content-Type: application/x-www-form-urlencoded

playlistID={playlist_id}&playlistName={name}
```

**Form Parameters**:

- `playlistID` (required): Spotify playlist ID
- `playlistName` (required): Display name for playlist

**Response**: `200 OK` + `"Success"`

**Side Effects**:

- Creates or updates `Playlists` record
- Creates `PlaylistsUsers` relationship
- Background worker will scan playlist on next cycle

---

#### Delete Playlist

Remove playlist from monitoring.

```http
POST /analytics/deletePlaylist/
Content-Type: application/x-www-form-urlencoded

playlistID={playlist_id}
```

**Form Parameters**:

- `playlistID` (required): Spotify playlist ID

**Response**: `200 OK` + `"Success"`

**Side Effects**:

- Deletes `PlaylistsUsers` relationship
- If no other users monitoring, deletes `Playlists` record

---

#### Get Playlist Songs

Get songs from a specific playlist.

```http
GET /analytics/playlistSongs/?playlistID={playlist_id}
```

**Query Parameters**:

- `playlistID` (required): Spotify playlist ID

**Response**:

```json
{
  "data": [
    {
      "song": "Song Name",
      "artists": "Artist 1, Artist 2",
      "songID": "7ouMYWpwJ422jRcDASZB7P"
    }
  ]
}
```

---

### Global Statistics

#### Global Stats

Get aggregated statistics across all users (cached 1 hour).

```http
GET /analytics/globalStats/
```

**Response**:

```json
{
  "totalPlays": 1234567,
  "uniqueSongs": 234567,
  "uniqueArtists": 45678,
  "totalUsers": 42,
  "topSongs": [
    {
      "song": "Song Name",
      "artists": "Artist 1, Artist 2",
      "plays": 456
    }
  ],
  "topArtists": [
    {
      "artist": "Artist Name",
      "plays": 789
    }
  ]
}
```

**Cache**: 1 hour (3600 seconds)

---

#### Global Daily Aggregation

Get listening stats aggregated by day across all users (cached 1 hour).

```http
GET /analytics/globalDailyAggregation/
```

**Response**:

```json
[
  {
    "date": "2024-01-15",
    "plays": 1234,
    "uniqueSongs": 567,
    "uniqueArtists": 234
  }
]
```

**Cache**: 1 hour (3600 seconds)

**Note**: Returns up to 365 days of data

---

#### Global Hourly Aggregation

Get listening stats aggregated by hour-of-day across all users (cached 1 hour).

```http
GET /analytics/globalHourlyAggregation/
```

**Response**:

```json
[
  {
    "hour": 14,
    "plays": 5678,
    "avgPlays": 15.6
  }
]
```

**Cache**: 1 hour (3600 seconds)

---

### Historical Data Import

#### Analyze Historical Import

Analyze uploaded Spotify data export and return statistics.

```http
POST /analytics/analyzeHistoricalImport/
Content-Type: multipart/form-data

file={zip_file}
```

**Form Parameters**:

- `file` (required): ZIP file from Spotify data export (Extended Streaming History)

**Response**:

```json
{
  "total_entries": 140000,
  "songs_to_import": 135000,
  "exact_duplicates": 1000,
  "window_duplicates": 2500,
  "sequential_duplicates": 1500,
  "filtered_short": 500,
  "filtered_incognito": 200,
  "year_breakdown": {
    "2020": 15000,
    "2021": 28000,
    "2022": 32000,
    "2023": 30000,
    "2024": 30000
  }
}
```

**Processing Time**: 30-120 seconds depending on data size

**Note**:

- Does NOT import data, only analyzes
- Filters songs <30 seconds, incognito sessions, podcasts
- Uses 3-phase duplicate detection (exact → 7.5min window → sequential)

---

#### Execute Historical Import

Import analyzed historical data.

```http
POST /analytics/executeHistoricalImport/
Content-Type: multipart/form-data

file={zip_file}
```

**Form Parameters**:

- `file` (required): Same ZIP file from Spotify data export

**Response**:

```json
{
  "success": true,
  "imported_songs": 135000,
  "processing_time_seconds": 245.67
}
```

**Processing Time**: 2-10 minutes depending on data size

**Side Effects**:

- Bulk creates `Artists` records
- Bulk creates `Songs` records (with artist relationships)
- Bulk creates `ListeningHistory` records
- Bulk updates `PlayCount` records

**Note**:

- Re-runs analysis to ensure consistency
- Processes in batches of 1000 to prevent memory issues
- Skips local files (IDs starting with `:`)

---

## Error Responses

### 401 Unauthorized

User not authenticated.

```json
{
  "error": "Authentication required"
}
```

**Common Causes**:

- No active session
- Session expired (>24 hours)
- User clicked logout

**Solution**: Redirect to `/analytics/login/`

---

### 400 Bad Request

Invalid request parameters.

```json
{
  "error": "Missing required parameter: playlistID"
}
```

**Common Causes**:

- Missing required form/query parameters
- Invalid parameter format

---

### 500 Internal Server Error

Server-side error.

```json
{
  "error": "Database connection failed"
}
```

**Common Causes**:

- Database unavailable
- Spotify API error
- Worker thread crash

---

## Rate Limiting

### Client-Side

No explicit rate limiting implemented. Use responsibly:

- **Listening History**: Poll every 5-10 seconds max
- **Stats Endpoints**: Poll every 30-60 seconds
- **Historical Import**: Once per session

### Server-Side (Spotify API)

Background workers handle Spotify rate limiting:

- **History Mode**: ~3 calls/hour/user (safe)
- **Realtime Mode**: ~720 calls/hour/user (approaching limits)
- **Retry Logic**: 60-second backoff on errors

---

## Pagination

Endpoints with pagination support `start` and `length` parameters:

- `/analytics/listeningHistory/`
- `/analytics/songs/`

**Example**:

```bash
# Get first 50 records
GET /analytics/listeningHistory/?start=0&length=50

# Get next 50 records
GET /analytics/listeningHistory/?start=50&length=50
```

**DataTables.js Integration**:

Frontend uses DataTables which automatically sends pagination parameters:

```javascript
$("#historyTable").DataTable({
  ajax: "/analytics/listeningHistory/",
  serverSide: true,
  columns: [{ data: "timePlayed" }, { data: "song" }, { data: "artists" }],
});
```

---

## CORS

CORS not enabled by default. If deploying frontend separately, add to `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
]
```

---

## Example Requests

### Get Recent Listening History

```bash
curl -X GET \
  'https://yourdomain.com/analytics/listeningHistory/?start=0&length=10' \
  -H 'Cookie: sessionid=abc123...'
```

### Start Monitoring Example

```bash
curl -X GET \
  'https://yourdomain.com/analytics/start/' \
  -H 'Cookie: sessionid=abc123...'
```

### Submit Playlist Example

```bash
curl -X POST \
  'https://yourdomain.com/analytics/playlistSubmission/' \
  -H 'Cookie: sessionid=abc123...' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'playlistID=37i9dQZF1DXcBWIGoYBM5M&playlistName=Today%27s%20Top%20Hits'
```

### Analyze Historical Data

```bash
curl -X POST \
  'https://yourdomain.com/analytics/analyzeHistoricalImport/' \
  -H 'Cookie: sessionid=abc123...' \
  -F 'file=@my_spotify_data.zip'
```
