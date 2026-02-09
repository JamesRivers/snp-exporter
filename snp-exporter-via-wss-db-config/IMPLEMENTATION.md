# SNP Exporter - Implementation Summary

## Overview
Added a web UI for managing SNP connections with SQLite database persistence, dual-port architecture, and real-time status monitoring.

## Changes Made

### New Files Created

1. **src/database.py** (7.5 KB)
   - SQLite database operations using aiosqlite
   - Schema: `snp_connections` and `connection_status` tables
   - CRUD operations: get, add, update, delete connections
   - Connection status tracking

2. **src/templates/index.html** (18.8 KB)
   - Bootstrap 5 UI for connection management
   - Real-time status indicators (🟢🔴🟡⚫)
   - Add/Edit/Delete connection modals
   - Dynamic object IDs builder with dropdowns
   - Auto-refresh every 5 seconds
   - Direct metrics endpoint links

### Modified Files

1. **src/main.py** (17.4 KB)
   - Refactored from single-port to dual-port architecture
   - Port 8000: Metrics only (Prometheus)
   - Port 8080: Web UI + Management API
   - Replaced YAML config reading with SQLite database queries
   - Worker now uses connection ID instead of name
   - Enhanced reloader for database polling (10s interval)
   - Added 6 REST API endpoints for connection management

2. **requirements.txt**
   - Added: `aiosqlite` (SQLite async support)
   - Added: `jinja2` (HTML templating)

3. **compose.yml**
   - Changed port mapping from `3800:8000` to `8000:8000, 8080:8080`
   - Updated environment variables:
     - Changed `INTERVAL=15` to `INTERVAL=5`
     - Added `POLL_INTERVAL=10`
     - Added `DB_PATH=/etc/snp_exporter/connections.db`
   - Removed obsolete `CONFIG_FILE` variable

4. **Dockerfile**
   - Updated COPY commands to properly include templates directory
   - Changed from `COPY src/ .` to separate Python files and templates

5. **README.md** (5.8 KB)
   - Completely rewritten with web UI documentation
   - Added API endpoint reference
   - Updated architecture description
   - Added environment variables table
   - Removed config.yml instructions

## Architecture Changes

### Before
```
Single FastAPI App (Port 3800)
├── /metrics (Prometheus)
└── /-/reload (Config reload)

Config: config.yml (YAML file)
```

### After
```
Dual FastAPI Apps
├── Port 8000 (Metrics Server)
│   ├── /metrics (Prometheus)
│   └── /-/reload (Trigger reload)
│
└── Port 8080 (UI Server)
    ├── / (Web UI - HTML)
    ├── /api/connections (List)
    ├── /api/connections/{id} (Get/Update/Delete)
    └── POST /api/connections (Add)

Config: connections.db (SQLite database)
```

## Key Features

### Web UI Capabilities
1. **View Connections**
   - Table with all connections
   - Real-time status: Connected, Disconnected, Connecting, Error
   - Last update timestamp
   - Enable/Disable toggle display

2. **Add Connection**
   - Form with validation
   - Dynamic object IDs builder:
     - Object type dropdown (ptp, system, ipVidRx, procChannelHD)
     - Element IP input
     - Conditional Object ID field
   - JSON preview of subscriptions

3. **Edit Connection**
   - Pre-populated form
   - Modify any field including credentials
   - Changes trigger worker restart

4. **Delete Connection**
   - Confirmation modal
   - Immediate worker shutdown
   - Metrics cleanup

5. **Metrics Link**
   - Direct button to Prometheus metrics endpoint
   - Target filtering available via labels

### Database Schema

**snp_connections**
- id (PRIMARY KEY)
- name (UNIQUE)
- restapi
- websocket
- username
- password
- objects_ids (JSON)
- enabled (BOOLEAN)
- created_at
- updated_at

**connection_status**
- connection_id (PRIMARY KEY, FOREIGN KEY)
- status (connected/disconnected/connecting/error)
- last_update

### Worker Lifecycle

1. **Start**: Reloader detects new enabled connection
2. **Connect**: Worker establishes WebSocket connection
3. **Authenticate**: Gets token from REST API
4. **Subscribe**: Sends subscription message with objects_ids
5. **Monitor**: Receives and parses status messages
6. **Update**: Writes status to database on each message
7. **Stop**: Disabled/deleted connections exit worker
8. **Restart**: Configuration changes trigger worker restart

### Status Updates

- **Throttled**: Max once per message to avoid DB flooding
- **Polling**: Reloader checks DB every 10 seconds
- **Auto-refresh**: UI polls API every 5 seconds
- **Immediate**: Add/Edit/Delete triggers event.set()

## API Endpoints

### UI Server (Port 8080)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI (HTML page) |
| GET | `/api/connections` | List all connections with status |
| GET | `/api/connections/{id}` | Get single connection details |
| POST | `/api/connections` | Add new connection |
| PUT | `/api/connections/{id}` | Update connection |
| DELETE | `/api/connections/{id}` | Delete connection |

### Metrics Server (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics` | Prometheus metrics |
| GET | `/-/reload` | Trigger config reload |

## Testing

Build and run:
```bash
docker compose build
docker compose up -d
```

Access:
- Web UI: http://localhost:8080/
- Metrics: http://localhost:8000/metrics

## Migration Notes

**From config.yml to SQLite:**
- No automatic migration included (as requested)
- Users start fresh with empty database
- Old config.yml can be referenced for manual entry
- Example config.yml preserved for reference

## Known Improvements

1. **Database location**: Persisted to volume mount at `/etc/snp_exporter/`
2. **Error handling**: Basic auth failure shown as "error" status
3. **Concurrent updates**: SQLite handles serialization
4. **Password visibility**: Credentials shown in UI for editing
5. **Status updates**: Throttled to once per message received

## Files Summary

```
exporter_snp/
├── src/
│   ├── main.py           (17.4 KB) - Main application, workers, API
│   ├── database.py       (7.5 KB)  - SQLite operations
│   └── templates/
│       └── index.html    (18.8 KB) - Web UI
├── compose.yml           (412 B)   - Docker compose config
├── Dockerfile            (212 B)   - Container build
├── requirements.txt      (84 B)    - Python dependencies
├── README.md             (5.8 KB)  - Documentation
└── config.yml            (482 B)   - Legacy config (reference only)
```

## Docker Image

- Base: python:slim
- Size: 263 MB
- Python version: 3.14
- Dependencies: 26 packages installed

## Configuration

All managed via web UI. Database persists to:
```
/etc/snp_exporter/connections.db
```

Volume mounted from project root, so database survives container restarts.
