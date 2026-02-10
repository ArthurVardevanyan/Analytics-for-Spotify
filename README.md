# Analytics for Spotify

![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/tests/badge.svg?branch=main)![Actions Status](https://github.com/ArthurVardevanyan/Analytics-for-Spotify/workflows/CodeQL/badge.svg?branch=main) [![Coverage Status](https://coveralls.io/repos/github/ArthurVardevanyan/Analytics-for-Spotify/badge.svg?branch=main)](https://coveralls.io/github/ArthurVardevanyan/Analytics-for-Spotify?branch=main)

A self-hosted Spotify listening history tracker with real-time monitoring, historical data import, and comprehensive analytics. Features intelligent duplicate detection, distributed worker architecture, and production-ready Kubernetes deployment.

## Features

### Core Functionality

- **Real-Time & Historical Tracking**: Monitor currently playing tracks (5s poll) or recently played (20min poll)
- **Multi-User Support**: Horizontal scaling with automatic worker load balancing across pods
- **Historical Data Import**: Bulk import from Spotify's Extended Streaming History with intelligent duplicate detection
- **Playlist Monitoring**: Daily scans with automatic song/artist discovery and relationship linking
- **Local File Support**: Track imported/local songs with deterministic custom ID generation
- **Global Statistics**: Public homepage with aggregated stats across all users (1-hour cache)

### Analytics

- **Play Count Leaderboards**: Most played songs and artists with sortable DataTables
- **Temporal Analysis**: Listening patterns aggregated by hour-of-day and date
- **Interactive Charts**: Chart.js visualizations with time range filtering (month/year/all-time)
- **Distribution Metrics**: Play count distributions and artist diversity charts
- **Dark/Light Theme**: Auto-detection with manual toggle (☀️ Light, ☾ Dark, ◐ Auto modes) and localStorage persistence

### Technical Highlights

- **3-Phase Duplicate Detection**: Exact timestamp → 7.5min window → time-bucketed sequential context (90-95% faster than naive O(n²))
- **Worker Heartbeat System**: Automatic detection and recovery from worker failures (90-second timeout)
- **OAuth Token Management**: Automatic refresh with Spotify API (1-hour access token expiry)
- **Graceful Degradation**: Continues operating with database/API failures, automatic retry logic
- **Production Ready**: Kubernetes deployment with GitOps (ArgoCD), CI/CD (Tekton), comprehensive security (NetworkPolicy, SecComp, read-only FS)

## Documentation

- **[Architecture Deep Dive](docs/ARCHITECTURE.md)**: System design, worker management, data flow, authentication, duplicate detection algorithm
- **[Complete API Reference](docs/API.md)**: All 32 endpoints with request/response examples, error codes, pagination
- **[Database Schema](docs/references.md)**: Table structures, relationships, constraints

## Quick Start

### Prerequisites

- Kubernetes cluster (tested on OpenShift 4.x)
- PostgreSQL database (Crunchy Operator recommended)
- Spotify Developer Application ([Create one here](https://developer.spotify.com/dashboard))

### 1. Create Spotify OAuth App

1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create App"
3. Set **Redirect URI**: `https://your-domain/spotify/loginResponse`
4. Note your **Client ID** and **Client Secret**

### 2. Deploy

Deploy using your method of choice, podman, kubernetes, local testing

### 3. Access Application

- **Public stats**: `https://your-domain/spotify/`
- **Login & dashboard**: Click "Log In" → Authorize with Spotify → Analytics dashboard

### 4. Enable Monitoring

After login:

1. Click "Start Monitoring" button
2. Background worker will pick up your account within 90 seconds
3. Listening history appears within 20 minutes (history mode) or 5 seconds (realtime mode)

### 5. Import Historical Data (Optional)

1. Request your Extended Streaming History from Spotify:
   - Visit [Spotify Privacy Settings](https://www.spotify.com/account/privacy/)
   - Select "Extended streaming history" (includes all-time data)
   - Wait 1-30 days for email with download link
2. Download ZIP file
3. In dashboard, click "Import Historical Data"
4. Upload ZIP file → Click "Analyze" to preview
5. Click "Import" to execute (takes 2-10 minutes depending on size)

## Development Setup

### Local Development

#### Setup PostgreSQL Database

```bash
# Create PostgreSQL data directory
sudo mkdir /mnt/postgres
sudo chown $USER:$USER /mnt/postgres
sudo chmod 777 /mnt/postgres

# Start PostgreSQL with podman-compose
podman-compose -f container/podman-compose.yaml up -d

# Tear down database (if needed)
podman-compose -f container/podman-compose.yaml down
sudo rm -rf /mnt/postgres
```

#### Setup Python Environment

```bash
# Clone repository
git clone https://github.com/ArthurVardevanyan/Analytics-for-Spotify.git
cd Analytics-for-Spotify

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SPOTIFY_CLIENT_ID=<your_client_id>
export SPOTIFY_CLIENT_SECRET=<your_client_secret>
export SPOTIFY_REDIRECT_URI=http://localhost:8000/spotify/loginResponse
export DATABASE_URL=postgresql://spotify:spotify@localhost:5432/spotify

# Run migrations (requires MIGRATIONS=True)
export MIGRATIONS=True
python manage.py migrate
export MIGRATIONS=False  # Can be disabled after migrations complete

# Start Django backend
python manage.py runserver

# In separate terminal: Start background worker
source venv/bin/activate
python monitoringBackend/spotify.py
```

Access: <http://localhost:8000/spotify/>

### Container Build

The project uses a **multi-stage build** architecture with separate base images for build-time and runtime:

```bash
# Build base images (rarely changes)
podman build -f container/containerfile-base-builder -t analytics-for-spotify:base-builder .
podman build -f container/containerfile-base-runtime -t analytics-for-spotify:base-runtime .

# Build application image (frequently)
podman build -t analytics-for-spotify:latest -f containerfile .
```

**Multi-Stage Benefits**:

- **~85-100MB smaller** final images (no gcc, pkg-config, pip in production)
- **Better security**: Build tools excluded from runtime containers
- **Faster rebuilds**: Base images cached, only app layer changes
- **Clean separation**: Builder has pip/gcc, runtime has only Apache + Python packages

**Base Images**:

- `base-builder`: Debian slim + python3-pip, gcc, pkg-config (for compiling packages)
- `base-runtime`: Debian slim + Apache, mod-wsgi, python3 (with security hardening)

See [containerfile](containerfile) for the multi-stage build configuration.

## Architecture Overview

```mermaid
graph TB
    Browser[Browser] --> Frontend

    subgraph Frontend
        Index[index.html - Public Stats]
        Analytics[analytics.html - Dashboard]
    end

    Frontend --> Django[Django Backend]

    Django --> DB[(PostgreSQL)]
    Django --> SpotifyAuth[Spotify OAuth]

    Workers[Background Workers] --> DB
    Workers --> SpotifyAPI[Spotify API]

    subgraph Workers
        Playlist[Playlist Scanner - Daily]
        History[History Monitor - 20min]
        Realtime[Realtime Monitor - 5s]
        Updater[Song ID Updater - Daily]
    end

    CronJob[Artist Linker CronJob] --> DB
    CronJob --> SpotifyAPI
```

### Key Components

- **Django Backend** (`webBackend/`): 32 REST API endpoints, OAuth management, historical import
- **Background Workers** (`monitoringBackend/`): Distributed worker pods with automatic load balancing
- **Frontend** (`webFrontend/`): Static HTML/JS with Chart.js and DataTables
- **Database**: PostgreSQL with 10 tables (users, songs, artists, listening history, playlists, play counts)
- **CronJob**: Daily artist linking for songs with missing metadata

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed system design.

## Tech Stack

| Component         | Technology              |
| ----------------- | ----------------------- |
| Backend Framework | Django                  |
| Database          | PostgreSQL              |
| Database ORM      | Django ORM              |
| Frontend Charts   | Chart.js                |
| Frontend Tables   | DataTables              |
| Container Runtime | Podman/Docker           |
| Orchestration     | Kubernetes/OpenShift    |
| CI/CD             | Tekton Pipelines        |
| GitOps            | ArgoCD                  |
| Web Server        | Apache + mod_wsgi       |
| Ingress           | OpenShift Route / Istio |
| Security          | Coraza WAF (WASM)       |

## Monitoring Modes

Choose monitoring mode based on your needs:

| Mode         | API Endpoint                      | Poll Frequency | API Calls/Hour | Pros                                   | Cons                                 |
| ------------ | --------------------------------- | -------------- | -------------- | -------------------------------------- | ------------------------------------ |
| **History**  | `/v1/me/player/recently-played`   | 20 minutes     | ~3             | Low API usage, Works offline           | 20-min delay                         |
| **Realtime** | `/v1/me/player/currently-playing` | 5 seconds      | ~720           | Real-time updates, Tracks local files  | High API usage, Offline incompatible |
| **Hybrid**   | Both endpoints                    | 20min + 5s     | ~723           | Local file tracking, Low API for local | High API usage                       |

**Recommendation**: Use **History mode** for most users. Switch to Hybrid only if you need local file tracking.

Set mode in user settings:

- `realtime=0`: History mode
- `realtime=1`: Realtime mode
- `realtime=2`: Hybrid mode

## Database Schema

```mermaid
erDiagram
    Users ||--o{ ListeningHistory : has
    Users ||--o{ PlayCount : has
    Users ||--o{ PlaylistsUsers : has
    Users ||--o{ Workers : manages

    Songs ||--o{ ListeningHistory : recorded_in
    Songs ||--o{ PlayCount : counted_in
    Songs ||--o{ PlaylistSongs : included_in
    Songs }o--o{ Artists : performed_by

    Playlists ||--o{ PlaylistSongs : contains
    Playlists ||--o{ PlaylistsUsers : monitored_by

    Users {
        string user PK
        string cache
        int realtime
        int enabled
        int statusSong
        int statusPlaylist
        int worker FK
    }

    Songs {
        string id PK
        string name
        string album
        datetime releaseDate
        int explicit
        many-to-many artists
    }

    Artists {
        string name PK
    }

    ListeningHistory {
        int id PK
        string user FK
        string songID FK
        datetime timePlayed
    }

    PlayCount {
        int id PK
        string user FK
        string songID FK
        int count
    }
```

**10 Tables**: `SpotifyAPI`, `Workers`, `Users`, `Artists`, `Songs`, `PlayCount`, `ListeningHistory`, `Playlists`, `PlaylistsUsers`, `PlaylistSongs`

See [Database Schema Documentation](docs/references.md) for complete field specifications.

## Configuration

### Environment Variables

```bash
# Required
SPOTIFY_CLIENT_ID=<your_spotify_client_id>
SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>
SPOTIFY_REDIRECT_URI=https://your-domain/spotify/loginResponse

# Optional
DATABASE_URL=postgresql://user:password@host:5432/dbname
DEBUG=False  # Default: False in production
ALLOWED_HOSTS=your-domain.com,*.your-domain.com  # Default: localhost
SECRET_KEY=<django_secret_key>  # Auto-generated if not set
```

### Django Settings

Key settings in [AnalyticsForSpotify/settings.py](AnalyticsForSpotify/settings.py):

- **Database**: PostgreSQL via `DATABASE_URL` environment variable
- **Session**: 24-hour expiry, database-backed
- **CSRF**: Trusted origins configured for production domain
- **Security**: `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000`
- **Caching**: 1-hour cache for global statistics endpoints

### Kubernetes Configuration

Kustomize overlays in `kubernetes/overlays/`:

- **okd-external/**: OpenShift with external Route (HTTPS via Let's Encrypt)
- **okd-knative/**: Serverless Knative deployment (scale-to-zero)
- **sno/**: Single-node OpenShift (development/testing)

Key configurations:

- **Replicas**: 2 (for high availability)
- **Resources**: 350m CPU / 1Gi memory limits
- **Security**: Non-root, read-only FS, drop all capabilities, SecComp
- **Networking**: NetworkPolicy restricts to PostgreSQL + internet egress only

## Deployment Options

### CI/CD with Tekton

Pipeline in `tekton/base/`:

1. **Lint**: Runs pylint and markdownlint
2. **Test**: Executes unit tests with coverage
3. **Build**: Builds container image with Buildah
4. **Push**: Pushes to container registry
5. **Update Manifest**: Updates Kustomize overlay with new image SHA

Trigger on git push to `production` branch.

## Security

### Network Policies

- **Default Deny**: All ingress/egress blocked by default
- **Allow PostgreSQL**: Egress to database on port 5432
- **Allow Internet**: Egress to Spotify API (HTTPS only)
- **Allow Ingress**: Only from Istio/OpenShift Router

### Pod Security

- **Non-root**: Runs as UID 1001
- **Read-only FS**: All filesystems read-only except `/tmp` and `/dev/shm`
- **Drop Capabilities**: All Linux capabilities dropped
- **SecComp**: Restricted syscall profile (`runtime/default`)

### WAF Protection

Coraza WAF (WASM plugin) on Istio gateway:

- **Request Body Inspection**: Disabled for `/analyzeHistoricalImport` and `/executeHistoricalImport` (allows large file uploads)
- **Memory Limit**: 512MB for WASM VM
- **Core Rule Set**: OWASP ModSecurity rules enabled for all other endpoints

### OAuth Security

- **PKCE**: Not currently implemented (client secret flow)
- **Token Storage**: Encrypted in database `users.cache` field (JSON)
- **Session Security**: HttpOnly, Secure cookies with 24-hour expiry
- **CSRF Protection**: Django CSRF middleware enabled

## Performance

### Optimizations

- **Time-Bucketed Duplicate Detection**: 15-minute buckets reduce O(n²) to O(n) for sequential context checks
- **Batch Database Operations**: Historical import processes 1000 records per transaction
- **Bulk Creates**: `bulk_create()` for artists, songs, listening history (single SQL INSERT)
- **Database Indexing**: Compound indexes on `(timestamp, user)` for listening history queries
- **Cache Headers**: 1-hour cache for global statistics endpoints (reduces DB load)
- **Worker Load Balancing**: Distributes users evenly across pods (automatic rebalancing on failures)

### Scalability

- **Horizontal Scaling**: Add more worker pods, automatic user redistribution
- **Recommendation**: ~10-20 users per worker pod
- **Database**: PostgreSQL with Crunchy Operator auto-scaling and backups
- **Stateless Backend**: All state in database, safe to restart/scale anytime

### Monitoring

- **Health Checks**: `/analytics/health/` (liveness), `/analytics/status/` (readiness with DB stats)
- **Worker Heartbeats**: 75-second cycle, auto-removal after 90 seconds without heartbeat
- **Status Fields**: `statusSong`, `statusPlaylist` track thread states (0=stopped, 1=running, 2=processing)
- **Logs**: Structured logging via Python `logging` module

## Screenshots

### Public Homepage

![Homepage with global statistics](img/AnalyticsForSpotifyHomePageSample.png)

### Personal Analytics Dashboard

![Dashboard with listening history and charts](img/AnalyticsForSpotifySample.png)

### Song/Playlist Distribution

![Song play and playlist distribution charts](img/SongPlayPlaylistDistribution.png)

### Historical Data Import

![Import interface with duplicate detection statistics](img/AnalyticsForSpotifyHistorical.png)

### Database Structure Diagram

![Database structure diagram](img/DatabaseStructure.png)

## FAQ

**Q: How do I request my Extended Streaming History from Spotify?**

A: Visit [Spotify Privacy Settings](https://www.spotify.com/account/privacy/) → Select "Extended streaming history" → Wait 1-30 days for email with download link.

**Q: Why isn't my listening history updating?**

A: Check:

1. Monitoring is enabled (click "Start Monitoring")
2. Worker pod is running (`kubectl get pods`)
3. Worker assigned to your user (`users.worker` field not NULL)
4. OAuth token valid (re-login if "access token expired" in logs)

**Q: How do I switch from realtime to history mode?**

A: Update `users.realtime` field in database:

```sql
UPDATE users SET realtime=0 WHERE user='<your_spotify_user_id>';
```

Background worker will pick up change on next cycle (~75 seconds).

**Q: Can I run this without Kubernetes?**

A: Yes, see [Development Setup](#development-setup). Requires:

- Python 3.11+
- PostgreSQL or SQLite
- Separate terminal for background worker

**Q: How do I backup my data?**

A: PostgreSQL backups via Crunchy Operator:

```bash
# Manual backup
kubectl exec -n analytics-for-spotify postgres-0 -- pg_dump -U postgres spotify_analytics > backup.sql

# Restore
kubectl exec -i -n analytics-for-spotify postgres-0 -- psql -U postgres spotify_analytics < backup.sql
```

Crunchy Operator also configures automated daily backups to S3.

## License

This project is licensed under the MIT License - see LICENSE file for details.

**Important**: While this code is MIT licensed, using this application requires compliance with [Spotify's Developer Terms of Service](https://developer.spotify.com/terms). Key restrictions include:

- ❌ **No commercial use** without a separate agreement with Spotify
- ❌ **No selling or transferring** user data obtained from Spotify API
- ✅ **Personal/educational use** is permitted
- ✅ **Self-hosting for yourself or small groups** is fine

The MIT license applies to the code in this repository. Spotify's terms apply to API usage.

## Acknowledgments

- Spotify for providing comprehensive APIs and data export tools
- Chart.js for excellent visualization library
- DataTables for powerful table interactions
- Crunchy Data for PostgreSQL Operator
