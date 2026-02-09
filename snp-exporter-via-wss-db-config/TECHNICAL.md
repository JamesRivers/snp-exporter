# SNP Exporter - Technical Documentation

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Code Structure](#code-structure)
- [Technical Interconnects](#technical-interconnects)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Metrics System](#metrics-system)
- [Worker Lifecycle](#worker-lifecycle)
- [API Endpoints](#api-endpoints)
- [WebSocket Protocol](#websocket-protocol)
- [Configuration Management](#configuration-management)

---

## Overview

The SNP Exporter is a Python-based Prometheus exporter that connects to Imagine Communications SNP (Signal Network Processor) devices via WebSocket, collects hardware and operational metrics, and exposes them in Prometheus format for monitoring and alerting.

The application features a web-based UI for managing multiple SNP connections, real-time connection status monitoring, and configuration import/export capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SNP Exporter Container                    │
│                                                              │
│  ┌────────────────────┐      ┌─────────────────────────┐   │
│  │  Metrics Server    │      │      UI Server          │   │
│  │   (Port 8000)      │      │     (Port 8080)         │   │
│  │                    │      │                         │   │
│  │  FastAPI App       │      │  FastAPI App            │   │
│  │  /metrics          │      │  /                      │   │
│  │  /-/reload         │      │  /api/connections       │   │
│  │                    │      │  /api/export            │   │
│  │  Prometheus Client │      │  /api/import            │   │
│  └────────────────────┘      └─────────────────────────┘   │
│           │                            │                     │
│           └────────────────┬───────────┘                     │
│                            │                                 │
│               ┌────────────▼──────────────┐                 │
│               │   Database Layer          │                 │
│               │   (SQLite - aiosqlite)    │                 │
│               │                           │                 │
│               │  ┌──────────────────────┐ │                 │
│               │  │ snp_connections      │ │                 │
│               │  │ connection_status    │ │                 │
│               │  └──────────────────────┘ │                 │
│               └────────────┬──────────────┘                 │
│                            │                                 │
│               ┌────────────▼──────────────┐                 │
│               │   Worker Pool (asyncio)   │                 │
│               │                           │                 │
│               │  Worker 1 ──┬─ WS Task   │                 │
│               │             └─ Proc Task  │                 │
│               │  Worker 2 ──┬─ WS Task   │                 │
│               │             └─ Proc Task  │                 │
│               │  Worker N ──┬─ WS Task   │                 │
│               │             └─ Proc Task  │                 │
│               └───────────────────────────┘                 │
│                      │              │                        │
│                      ▼              ▼                        │
└──────────────────────┼──────────────┼────────────────────────┘
                       │              │
                  WebSocket        REST API
                   (WSS)           (HTTPS)
                       │              │
                       ▼              ▼
              ┌─────────────────────────────┐
              │    SNP Devices              │
              │  192.168.90.23/smm          │
              │  192.168.90.33/smm          │
              │  192.168.x.x/smm            │
              └─────────────────────────────┘
```

### Component Breakdown

#### 1. Dual FastAPI Servers
Two independent FastAPI applications run concurrently:

**Metrics Server (Port 8000)**
- Purpose: Prometheus metrics endpoint only
- Routes: `/metrics`, `/-/reload`
- Used by: Prometheus scraper, monitoring tools
- Security: Read-only, no authentication

**UI Server (Port 8080)**
- Purpose: Web interface and connection management
- Routes: HTML UI, REST API endpoints
- Used by: Administrators, automation scripts
- Security: Future authentication planned

#### 2. Database Layer (SQLite)
Persistent storage using aiosqlite (async SQLite):

**Tables:**
- `snp_connections`: Connection configurations
- `connection_status`: Real-time connection states

**Operations:**
- CRUD via async functions
- Foreign key constraints
- Automatic timestamp management

#### 3. Worker Pool
Async worker tasks managed by asyncio.TaskGroup:

**Per-Worker Tasks:**
- WebSocket listener (primary)
- Processor personality poller (background, 60s interval)

**Worker Lifecycle:**
- Created by reloader when connection enabled
- Cancelled when connection disabled/deleted
- Restarted on configuration changes

#### 4. Reloader Task
Configuration monitor that polls database every 10 seconds:

**Responsibilities:**
- Detect new/removed/modified connections
- Start/stop/restart workers accordingly
- Trigger metric cleanup on removal

---

## Technology Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| **Python** | 3.14 | Runtime environment |
| **FastAPI** | Latest | Web framework for HTTP servers |
| **Uvicorn** | Latest | ASGI server for FastAPI |
| **aiosqlite** | Latest | Async SQLite database driver |
| **aiohttp** | Latest | Async HTTP client for REST API calls |
| **websockets** | Latest | WebSocket client for SNP communication |
| **prometheus_client** | Latest | Prometheus metrics library |
| **pyyaml** | Latest | YAML parsing (legacy config support) |
| **jinja2** | Latest | HTML templating for web UI |

### Infrastructure

| Component | Technology |
|-----------|------------|
| **Container** | Docker |
| **Orchestration** | Docker Compose |
| **Database** | SQLite 3 |
| **Web Server** | Uvicorn ASGI |
| **Async Runtime** | asyncio (Python stdlib) |

---

## Code Structure

```
exporter_snp/
├── src/
│   ├── main.py              # Main application entry point
│   │   ├── FastAPI app definitions (metrics + UI)
│   │   ├── API route handlers
│   │   ├── Worker functions
│   │   ├── Metrics parsing logic
│   │   └── Main orchestration
│   │
│   ├── database.py          # SQLite database operations
│   │   ├── Schema creation
│   │   ├── CRUD operations
│   │   ├── Status tracking
│   │   └── Connection management
│   │
│   └── templates/
│       └── index.html       # Web UI (Bootstrap 5)
│           ├── Connection table
│           ├── Add/Edit modals
│           ├── Export/Import handlers
│           └── JavaScript logic
│
├── compose.yml              # Docker Compose configuration
├── Dockerfile               # Container build instructions
├── requirements.txt         # Python dependencies
├── README.md                # Quick start guide
├── TECHNICAL.md             # This file
└── OPERATIONS.md            # Operational user guide
```

### File Responsibilities

#### src/main.py (547 lines)

**Global Variables:**
- Prometheus metric objects (Gauge, Counter, Info)
- FastAPI app instances (app, ui_app)
- Jinja2 templates instance
- asyncio.Event for reload signaling

**Functions:**

| Function | Lines | Purpose |
|----------|-------|---------|
| `reload()` | 64-66 | Trigger config reload via event |
| `index()` | 68-70 | Serve HTML UI |
| `get_connections_api()` | 72-79 | List all connections with status |
| `get_connection_api()` | 81-90 | Get single connection details |
| `add_connection_api()` | 92-101 | Add new connection |
| `update_connection_api()` | 103-114 | Update connection |
| `delete_connection_api()` | 116-125 | Delete connection |
| `export_connections()` | 127-149 | Export configs as JSON |
| `import_connections()` | 151-206 | Import configs from JSON |
| `processor_personality_poller()` | 208-228 | Poll processor personalities |
| `worker()` | 230-357 | Main WebSocket worker |
| `safe_float()` | 359-362 | Convert values to float safely |
| `parse_statuses()` | 364-395 | Parse SNP status messages |
| `get_token()` | 397-413 | Fetch authentication token |
| `get_processor_personality()` | 415-444 | Fetch processor config |
| `remove_metrics()` | 446-461 | Clean up Prometheus metrics |
| `reloader()` | 463-512 | Monitor DB for config changes |
| `main()` | 514-534 | Application entry point |

**Prometheus Metrics Defined:**
- `api_status` - Connection status (Gauge)
- `received_count` - Message counter (Counter)
- `received_duration` - Processing time (Gauge)
- `temperature_mainboard` - Temperature (Gauge)
- `temperature_ioboard` - Temperature (Gauge)
- `powersupply_status` - Power status (Gauge)
- `hardware_stats` - Hardware info (Info)
- `major_alarms` - Alarm count (Gauge)
- `minor_alarms` - Alarm count (Gauge)
- `fpga_temperature` - Temperature with index (Gauge)
- `fpga_fan_status` - Fan status with index (Gauge)
- `front_fan_status` - Fan status with index (Gauge)
- `qsfp_temperature` - Temperature with index (Gauge)
- `ptp_status` - PTP state (Gauge)
- `ptp_master_offset` - PTP offset (Gauge)
- `ptp_master_delay` - PTP delay (Gauge)
- `video_rx` - Video info with index (Info)
- `aco_abstatus` - ACO A/B status with index (Gauge)
- `processor_personality` - Processor type (Info)

#### src/database.py (229 lines)

**Functions:**

| Function | Purpose |
|----------|---------|
| `init_db()` | Initialize database and create tables |
| `get_db_connection()` | Create async SQLite connection |
| `create_tables()` | Create schema if not exists |
| `get_connections()` | Fetch all connections with status |
| `get_connection_by_id()` | Fetch single connection by ID |
| `get_connection_by_name()` | Fetch single connection by name |
| `add_connection()` | Insert new connection |
| `update_connection()` | Update connection fields |
| `delete_connection()` | Remove connection |
| `update_connection_status()` | Update connection status |
| `get_connection_status()` | Get current connection status |
| `get_enabled_connections()` | Fetch only enabled connections |

**Database Path:**
- Default: `/etc/snp_exporter/connections.db`
- Configurable via `DB_PATH` environment variable
- Persisted to Docker volume mount

#### src/templates/index.html (550+ lines)

**HTML Structure:**
- Bootstrap 5 navbar
- Connection table with status indicators
- Add/Edit connection modal with form
- Delete confirmation modal
- Hidden file input for import

**JavaScript Functions:**

| Function | Purpose |
|----------|---------|
| `loadConnections()` | Fetch and display connections |
| `renderConnections()` | Render connection table rows |
| `saveConnection()` | Add or update connection |
| `editConnection()` | Load connection for editing |
| `confirmDelete()` | Show delete confirmation |
| `reloadConfig()` | Trigger manual reload |
| `exportConfig()` | Download config as JSON |
| `importConfig()` | Upload and import JSON |
| `addObjectId()` | Add object to subscription list |
| `removeObject()` | Remove object from list |
| `renderObjectsTable()` | Display object subscriptions |
| `updatePreview()` | Show JSON preview |
| `showReloadAlert()` | Display reload notification |
| `showImportAlert()` | Display import summary |

**Auto-Refresh:**
- Polls `/api/connections` every 5 seconds
- Updates status indicators in real-time
- No page reload required

---

## Technical Interconnects

### 1. FastAPI ↔ Database

**Pattern: Async/Await**
```python
@ui_app.get("/api/connections")
async def get_connections_api():
    connections = await db.get_connections()  # Async DB call
    return JSONResponse(content=connections)
```

**Connection Pool:**
- Each database function creates its own connection
- Connections auto-closed after operation
- aiosqlite handles connection pooling

### 2. FastAPI ↔ Prometheus

**Pattern: ASGI Middleware**
```python
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()  # Create Prometheus ASGI app
app.mount("/metrics", metrics_app)  # Mount under /metrics path
```

**Metric Updates:**
- Metrics updated directly in worker functions
- Thread-safe via Prometheus client library
- No explicit locking required

### 3. Workers ↔ WebSocket

**Pattern: Async Context Manager**
```python
async with websockets.connect(uri, ssl=ssl_context) as websocket:
    await websocket.send(token)  # Send auth
    await websocket.send(subscription)  # Send subscription
    
    while True:
        message = await websocket.recv()  # Receive messages
        # Process and update metrics
```

**SSL Configuration:**
```python
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False  # SNP uses self-signed certs
ssl_context.verify_mode = ssl.CERT_NONE  # Disable verification
```

### 4. Workers ↔ REST API

**Pattern: Async HTTP Client**
```python
async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
    resp = await session.post(auth_url, json=credentials)
    token = await resp.text()
```

**Authentication Flow:**
1. POST to `/api/auth` with username/password
2. Receive JWT Bearer token
3. Use token in WebSocket handshake
4. Use token for processor config requests

### 5. Reloader ↔ Workers

**Pattern: Event-Driven + Polling**
```python
# Reloader triggers event
event.set()

# Workers wait for event
await event.wait()

# Reloader also polls DB every 10s
while True:
    await event.wait()
    # Check for changes
    event.clear()
    await asyncio.sleep(poll_interval)
    event.set()
```

**Worker Management:**
```python
active_connections: Dict[int, asyncio.Task] = {}

# Start new worker
task = group.create_task(worker(conn_id, interval), name=f"worker_{conn_id}")
active_connections[conn_id] = task

# Stop worker
task.cancel()
await task  # Wait for cancellation
del active_connections[conn_id]
```

### 6. UI ↔ Backend

**Pattern: REST API (JSON)**
```javascript
// Frontend
const response = await fetch('/api/connections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(connectionData)
});

// Backend
@ui_app.post("/api/connections")
async def add_connection_api(request: Request):
    data = await request.json()
    conn_id = await db.add_connection(data)
    event.set()  # Trigger reload
    return JSONResponse(content={"id": conn_id})
```

---

## Data Flow

### Connection Addition Flow

```
User clicks "Add Connection" button
    │
    ▼
JavaScript validates form data
    │
    ▼
POST /api/connections with JSON payload
    │
    ▼
FastAPI handler receives request
    │
    ▼
Database: INSERT INTO snp_connections
    │
    ▼
event.set() triggers reloader
    │
    ▼
Reloader polls database (within 10s)
    │
    ▼
Detects new connection ID
    │
    ▼
Creates new asyncio worker task
    │
    ├─▶ WebSocket task connects to SNP
    │   ├─ Authenticate with token
    │   ├─ Subscribe to objectIds
    │   └─ Receive and parse messages
    │
    └─▶ Processor personality task
        ├─ Sleep 60 seconds
        ├─ Fetch processorA/B/C/D configs
        └─ Update personality metrics
```

### Metrics Update Flow

```
SNP Device sends WebSocket message
    │
    ▼
Worker receives via websocket.recv()
    │
    ▼
JSON.parse(message)
    │
    ▼
Extract msgType
    │
    ├─ "statusState" or "allStatuses"
    │   │
    │   ▼
    │   Parse each status in statuses array
    │   │
    │   ├─ type="system"
    │   │   └─ Update: temperature, power, fans, alarms
    │   │
    │   ├─ type="ptp"
    │   │   └─ Update: ptp_status, offset, delay
    │   │
    │   ├─ type="ipVidRx"
    │   │   └─ Update: video_rx info
    │   │
    │   └─ type="procChannelHD"
    │       └─ Update: aco_abstatus
    │
    ├─ "fmmStatus" → Skip
    ├─ "permissionMessage" → Skip
    └─ "logState" → Skip
    │
    ▼
Metrics updated in Prometheus registry
    │
    ▼
Next Prometheus scrape returns new values
```

### Processor Personality Flow

```
Personality poller task starts
    │
    ▼
Sleep 60 seconds (initial delay)
    │
    ▼
Loop every 60 seconds:
    │
    ├─ Get authentication token
    │   │
    │   ▼
    │   POST /api/auth → JWT token
    │
    ├─ For each processor (A, B, C, D):
    │   │
    │   ▼
    │   GET /api/elements/{ip}/config/{processor}
    │   │
    │   ▼
    │   Parse response.config JSON
    │   │
    │   ▼
    │   Extract config.general.personality
    │   │
    │   ▼
    │   processor_personality.labels(target, processor).info({"personality": value})
    │
    └─ Continue loop or cancel if worker stops
```

---

## Database Schema

### snp_connections Table

```sql
CREATE TABLE IF NOT EXISTS snp_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    restapi TEXT NOT NULL,
    websocket TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    objects_ids TEXT NOT NULL,  -- JSON array as string
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Auto-increment primary key
- `name`: Unique connection identifier (used as Prometheus label)
- `restapi`: Authentication endpoint URL
- `websocket`: WebSocket endpoint URL
- `username`: SNP device username
- `password`: SNP device password (plaintext)
- `objects_ids`: JSON array of subscription objects
- `enabled`: Boolean (1=enabled, 0=disabled)
- `created_at`: Row creation timestamp
- `updated_at`: Last modification timestamp

**Example Row:**
```json
{
  "id": 1,
  "name": "SNP-192.168.90.23",
  "restapi": "https://192.168.90.23:9089/api/auth",
  "websocket": "wss://192.168.90.23/smm",
  "username": "admin",
  "password": "password",
  "objects_ids": "[{\"elementIP\":\"127.0.0.1\",\"objectType\":\"ptp\"}]",
  "enabled": 1,
  "created_at": "2026-02-03 20:00:00",
  "updated_at": "2026-02-03 20:00:00"
}
```

### connection_status Table

```sql
CREATE TABLE IF NOT EXISTS connection_status (
    connection_id INTEGER PRIMARY KEY,
    status TEXT NOT NULL,  -- 'connected', 'disconnected', 'connecting', 'error'
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES snp_connections(id) ON DELETE CASCADE
);
```

**Status Values:**
- `connected`: WebSocket authenticated and receiving messages
- `disconnected`: Connection lost, retrying
- `connecting`: Establishing connection
- `error`: Authentication failed or unrecoverable error

**Cascade Delete:**
When connection is deleted from `snp_connections`, corresponding status row is automatically removed.

---

## Metrics System

### Prometheus Client Integration

**Library Used:** `prometheus_client`

**Metric Types:**

1. **Gauge** - Values that can go up or down
   ```python
   temperature_mainboard = Gauge('ic_snp_mainboard_temperature', 'Main board temperature', ['target'])
   temperature_mainboard.labels(target="SNP-192.168.90.23").set(49.0)
   ```

2. **Counter** - Monotonically increasing values
   ```python
   received_count = Counter('ic_snp_received_count', 'SNP WebSocket received messages', ['target'])
   received_count.labels(target="SNP-192.168.90.23").inc()
   ```

3. **Info** - Key-value metadata
   ```python
   hardware_stats = Info('ic_snp_hardware', 'Hardware Stats information', ['target'])
   hardware_stats.labels(target="SNP-192.168.90.23").info({
       "firmware": "3.2.0.35",
       "hardware": "1.0",
       "serial": "2118370072"
   })
   ```

### Registry Customization

**Disabled default collectors:**
```python
REGISTRY.unregister(GC_COLLECTOR)  # Python garbage collection
REGISTRY.unregister(PLATFORM_COLLECTOR)  # Platform info
REGISTRY.unregister(PROCESS_COLLECTOR)  # Process stats
```

**Reason:** SNP-specific metrics only, reduce noise in Prometheus.

### Metric Naming Convention

**Pattern:** `ic_snp_{metric_name}_{unit}`

**Examples:**
- `ic_snp_mainboard_temperature` (implicit celsius)
- `ic_snp_last_received_duration_seconds` (explicit unit)
- `ic_snp_ptp_status` (boolean as 0/1)

### Label Strategy

**Common Labels:**
- `target`: Connection name (always present)
- `index`: Array index for multi-instance metrics
- `processor`: Processor identifier (A/B/C/D)
- `personality`: Processor type (in Info metrics)

**Label Cardinality:**
- `target`: 1-100 (number of SNP connections)
- `index`: 0-16 (hardware instances like FPGAs, fans)
- `processor`: 4 (A, B, C, D)

---

## Worker Lifecycle

### State Machine

```
┌─────────┐
│ CREATED │ Reloader detects new enabled connection
└────┬────┘
     │
     ▼
┌──────────────┐
│  CONNECTING  │ Worker attempts WebSocket connection
└──────┬───────┘
       │
       ├─ Success ──▶ CONNECTED
       │
       └─ Failure ──▶ ERROR or DISCONNECTED
                      │
                      └─ Retry after delay

┌───────────┐
│ CONNECTED │ WebSocket authenticated, receiving messages
└─────┬─────┘
      │
      ├─ Message received ──▶ Update metrics, stay CONNECTED
      │
      ├─ Connection lost ──▶ DISCONNECTED, retry
      │
      ├─ Config changed ──▶ CANCELLED, new worker created
      │
      └─ Disabled/Deleted ──▶ CANCELLED, EXIT

┌─────────────┐
│ DISCONNECTED│ Retrying connection
└──────┬──────┘
       │
       └─ After delay ──▶ Back to CONNECTING

┌─────────┐
│  ERROR  │ Unrecoverable error (bad credentials, invalid URI)
└────┬────┘
     │
     └─ Retry with exponential backoff

┌───────────┐
│ CANCELLED │ Worker stopped by reloader
└─────┬─────┘
      │
      └─ EXIT (task terminates)
```

### Concurrent Tasks per Worker

Each worker spawns two async tasks:

**1. WebSocket Listener (Primary)**
```python
async with websockets.connect(uri) as websocket:
    await websocket.send(token)
    await websocket.send(subscription)
    
    while True:
        message = await websocket.recv()
        # Parse and update metrics
```

**2. Processor Personality Poller (Background)**
```python
async def processor_personality_poller(...):
    while True:
        await asyncio.sleep(60)
        # Fetch processor A/B/C/D personalities
        # Update metrics
```

**Coordination:**
- Both tasks run concurrently via asyncio
- Personality task cancelled when WebSocket disconnects
- Proper cleanup via try/finally blocks

### Error Recovery

**Scenario: WebSocket disconnects**
```python
except websockets.exceptions.ConnectionClosed:
    api_status.labels(target=name).set(0.0)  # Mark as down
    await db.update_connection_status(conn_id, "disconnected")
    logger.error(f"Worker {name} disconnected, retrying...")
    await asyncio.sleep(3 * interval)  # Exponential backoff
    break  # Exit inner loop, reconnect in outer loop
```

**Scenario: Authentication fails**
```python
token = await get_token(...)
if not token:
    await db.update_connection_status(conn_id, "error")
    await asyncio.sleep(interval)
    continue  # Retry outer loop
```

**Scenario: Invalid URI**
```python
except websockets.exceptions.InvalidURI:
    api_status.labels(target=name).set(0.0)
    await db.update_connection_status(conn_id, "error")
    await asyncio.sleep(interval)  # Wait before retry
```

---

## WebSocket Protocol

### SNP WebSocket Communication

**Endpoint:** `wss://{device_ip}/smm`

**Message Format:** JSON

### Authentication Sequence

```
Client                          SNP Device
  │                                 │
  ├──── WebSocket CONNECT ─────────▶│
  │                                 │
  │◀──── 101 Switching Protocols ───┤
  │                                 │
  ├──── Bearer {JWT_TOKEN} ─────────▶│
  │                                 │
  │◀──── permissionsMsg ─────────────┤ (Authentication success)
  │                                 │
```

### Subscription Sequence

```
Client                          SNP Device
  │                                 │
  ├──── statusListSubscribe ───────▶│
  │     {                           │
  │       msgType: "statusListSubscribe",
  │       frequency: 1000,          │
  │       objectIds: [...]          │
  │     }                           │
  │                                 │
  │◀──── allStatuses ────────────────┤ (Initial dump)
  │                                 │
  │◀──── statusState ────────────────┤ (Periodic updates)
  │                                 │
  │◀──── statusState ────────────────┤ (Every 1000ms)
  │                                 │
```

### Message Types Handled

| msgType | Action | Frequency |
|---------|--------|-----------|
| `permissionsMsg` | Ignored | On auth |
| `fmmStatus` | Ignored | Periodic |
| `logState` | Ignored | On change |
| `allStatuses` | Parse all statuses | On subscribe |
| `statusState` | Parse status updates | Every 1s |
| `activeAlarmStatus` | Logged only | On alarm |

### Object ID Structure

```json
{
  "elementIP": "127.0.0.1",
  "objectType": "ptp|system|ipVidRx|procChannelHD",
  "objectId": "A-HD-1"  // Required only for procChannelHD
}
```

**Element IP:**
- Usually `127.0.0.1` (internal SNP IP)
- Can be actual device IP for specific routing

**Object Types:**
- `ptp`: PTP timing status
- `system`: Hardware health metrics
- `ipVidRx`: IP video receiver status
- `procChannelHD`: Processing channel with objectId

---

## Configuration Management

### Event-Driven Reload

**Event Object:**
```python
event = asyncio.Event()
```

**Trigger Points:**
1. Application startup: `event.set()`
2. Manual reload: `GET /-/reload` → `event.set()`
3. Add connection: `POST /api/connections` → `event.set()`
4. Update connection: `PUT /api/connections/{id}` → `event.set()`
5. Delete connection: `DELETE /api/connections/{id}` → `event.set()`
6. Periodic: Every 10 seconds

**Reloader Logic:**
```python
async def reloader(group, interval, poll_interval):
    active_connections = {}
    connection_data = {}
    
    while True:
        await event.wait()  # Wait for trigger
        
        # Get current enabled connections from DB
        connections = await db.get_enabled_connections()
        current_ids = set(conn["id"] for conn in connections)
        active_ids = set(active_connections.keys())
        
        # Calculate differences
        new_ids = current_ids - active_ids        # Start these
        removed_ids = active_ids - current_ids    # Stop these
        
        # Stop removed workers
        for conn_id in removed_ids:
            task.cancel()
            await task
            remove_metrics(name)
        
        # Start new workers
        for conn_id in new_ids:
            task = group.create_task(worker(conn_id, interval))
            active_connections[conn_id] = task
        
        # Restart changed workers
        for conn in connections:
            if config_changed:
                old_task.cancel()
                new_task = group.create_task(worker(conn_id, interval))
        
        event.clear()  # Reset event
        await asyncio.sleep(poll_interval)  # Wait 10s
        event.set()  # Auto-trigger
```

### Configuration Change Detection

**Comparison Strategy:**
- Store connection name per worker
- Compare old name vs new name
- If different, restart worker

**Why Name-Based:**
- Name changes are rare but significant
- Simple comparison (string equality)
- Avoids deep object comparison

**Alternative Approaches Considered:**
- Hash entire config: More accurate but complex
- Timestamp comparison: Doesn't detect manual DB edits
- JSON diff: Overkill for simple use case

---

## API Endpoints

### Metrics API (Port 8000)

#### GET /metrics
Returns Prometheus metrics in text format.

**Response Format:**
```
# HELP metric_name Description
# TYPE metric_name gauge|counter|info
metric_name{label1="value1",label2="value2"} 123.45
```

**Caching:** None (real-time)
**Authentication:** None
**Rate Limiting:** None

#### GET /-/reload
Triggers immediate configuration reload.

**Response:** Plain text "config reloaded"
**Side Effect:** Sets `event` to wake reloader

### UI API (Port 8080)

#### GET /
Serves HTML web interface using Jinja2 templates.

**Response:** HTML page
**Template:** `templates/index.html`

#### GET /api/connections
Returns all connections with status.

**Response Example:**
```json
[
  {
    "id": 1,
    "name": "SNP-192.168.90.23",
    "restapi": "https://192.168.90.23:9089/api/auth",
    "websocket": "wss://192.168.90.23/smm",
    "username": "admin",
    "password": "password",
    "objects_ids": [...],
    "enabled": true,
    "created_at": "2026-02-03 20:00:00",
    "updated_at": "2026-02-03 20:00:00",
    "status": "connected",
    "last_update": "2026-02-03 20:05:00"
  }
]
```

#### GET /api/connections/{id}
Returns single connection (excludes status).

**Use Case:** Load connection for editing

#### POST /api/connections
Creates new connection.

**Request Body:**
```json
{
  "name": "SNP-192.168.90.23",
  "restapi": "https://192.168.90.23:9089/api/auth",
  "websocket": "wss://192.168.90.23/smm",
  "username": "admin",
  "password": "password",
  "objects_ids": [
    {"elementIP": "127.0.0.1", "objectType": "ptp"}
  ],
  "enabled": true
}
```

**Response:**
```json
{"id": 1, "message": "Connection added"}
```

**Side Effect:** Triggers `event.set()` for reload

#### PUT /api/connections/{id}
Updates existing connection.

**Request Body:** Same as POST (partial updates not supported)

**Side Effect:** Triggers `event.set()`, worker restarts

#### DELETE /api/connections/{id}
Deletes connection.

**Response:**
```json
{"message": "Connection deleted"}
```

**Side Effect:** 
- Triggers `event.set()`
- Worker cancelled
- Metrics removed

#### GET /api/export
Exports all connections as JSON.

**Response:**
```json
{
  "version": "1.0",
  "exported_at": "2026-02-03 20:00:00",
  "connections": [...]
}
```

**Exclusions:** id, status, timestamps (clean export)

#### POST /api/import
Imports connections from JSON.

**Request Body:**
```json
{
  "version": "1.0",
  "connections": [...]
}
```

**Response:**
```json
{
  "message": "Import completed",
  "imported": 5,
  "skipped": 2,
  "errors": ["Connection 'foo' already exists, skipped"]
}
```

**Behavior:**
- Validates required fields
- Skips duplicates (by name)
- Triggers reload if any imported

---

## asyncio Task Management

### TaskGroup Usage

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(metrics_server.serve(), name="metrics")
    tg.create_task(ui_server.serve(), name="ui")
    tg.create_task(reloader(tg, interval, poll_interval), name="reloader")
    # Reloader creates worker tasks dynamically
```

**Benefits:**
- Automatic exception propagation
- Coordinated cancellation
- Structured concurrency

**Task Naming:**
- `metrics`: Uvicorn server on port 8000
- `ui`: Uvicorn server on port 8080
- `reloader`: Configuration monitor
- `worker_{conn_id}`: SNP connection worker
- `personality_{conn_id}`: Processor poller

### Task Cancellation

**Graceful Shutdown:**
```python
task.cancel()
try:
    await task
except asyncio.CancelledError:
    pass  # Expected
```

**Why Await After Cancel:**
- Ensures task has fully terminated
- Allows cleanup code to run (finally blocks)
- Prevents resource leaks

---

## Performance Characteristics

### Resource Usage

**Per Connection:**
- 1 WebSocket connection (persistent)
- 1 asyncio task (WebSocket listener)
- 1 asyncio task (personality poller)
- 4 REST API calls every 60 seconds
- ~1-5 KB/s bandwidth (status messages)

**Total (10 connections):**
- 10 WebSocket connections
- 20 asyncio tasks
- 40 REST API calls/minute
- ~10-50 KB/s bandwidth

### Scalability

**Theoretical Limits:**
- asyncio can handle 1000+ concurrent tasks
- SQLite can handle 100+ connections easily
- Limited by network bandwidth and SNP device capacity

**Practical Limits:**
- 50-100 SNP connections recommended
- Database queries are fast (<1ms)
- WebSocket overhead is minimal

### Optimization Strategies

1. **Async I/O:** All network operations are non-blocking
2. **Connection Pooling:** aiohttp session reuse
3. **Lazy Polling:** Processors polled only every 60s
4. **Event-Driven:** Reload triggered on change, not constant polling
5. **Indexed Queries:** Database uses primary key lookups

---

## Security Considerations

### Current Security Posture

**Weak Points:**
- ❌ No authentication on UI (port 8080)
- ❌ Passwords stored in plaintext (database + export)
- ❌ SSL verification disabled (SNP self-signed certs)
- ❌ No rate limiting on API endpoints
- ❌ No CORS protection

**Acceptable For:**
- Internal networks only
- Trusted users
- Non-production environments

### Recommended Hardening (Future)

1. **Authentication:**
   - Add HTTP Basic Auth or OAuth2
   - JWT tokens for API access
   - Role-based access control

2. **Encryption:**
   - Encrypt passwords in database
   - Use secrets management (Vault, etc.)
   - Enable SSL cert validation with proper CA

3. **Network Security:**
   - Firewall rules (restrict port 8080)
   - VPN/tunnel for remote access
   - HTTPS for UI server

4. **Input Validation:**
   - Sanitize all user inputs
   - Validate URL formats
   - Limit connection name length

---

## Environment Variables

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| `LOGGING` | INFO | String | Log level: DEBUG, INFO, WARNING, ERROR |
| `INTERVAL` | 5 | Integer | WebSocket message processing interval (seconds) |
| `POLL_INTERVAL` | 10 | Integer | Database polling interval for config changes (seconds) |
| `DB_PATH` | `/etc/snp_exporter/connections.db` | String | SQLite database file path |

**Configuration in compose.yml:**
```yaml
environment:
  - LOGGING=INFO
  - INTERVAL=5
  - POLL_INTERVAL=10
  - DB_PATH=/etc/snp_exporter/connections.db
```

---

## Docker Configuration

### Dockerfile Analysis

```dockerfile
FROM python:slim                    # Minimal Python 3.14 base
WORKDIR /code                       # Set working directory
COPY requirements.txt .             # Copy dependencies first (layer caching)
RUN pip install -r requirements.txt # Install dependencies
COPY src/*.py .                     # Copy Python source files
COPY src/templates/ ./templates/    # Copy HTML templates
CMD ["python", "-u", "main.py"]     # Run unbuffered
```

**Layer Optimization:**
- Dependencies installed before code copy
- Changes to code don't rebuild dependencies
- Templates in separate COPY for clarity

**Unbuffered Output (`-u`):**
- Immediate log output
- No buffering delays
- Better for `docker logs` viewing

### compose.yml Analysis

```yaml
services:
  snp_exporter:
    build:
      context: .
      dockerfile: Dockerfile
    image: snp_exporter:latest
    container_name: observe-snpexporter
    hostname: observe-snpexporter
    ports:
      - "8000:8000"   # Metrics
      - "8080:8080"   # UI
    environment:
      - LOGGING=INFO
      - INTERVAL=5
      - POLL_INTERVAL=10
      - DB_PATH=/etc/snp_exporter/connections.db
    volumes:
      - ./:/etc/snp_exporter/  # Persist database
```

**Volume Mount:**
- Maps project directory to `/etc/snp_exporter/`
- Database persists across container restarts
- Configuration changes visible inside container

---

## Logging Strategy

### Log Levels

**INFO (Default):**
- Worker start/stop
- Connection events
- Message type received
- Configuration changes

**DEBUG:**
- Token contents
- Full message payloads
- Detailed parsing steps

**WARNING:**
- Deprecated features
- Non-critical failures

**ERROR:**
- Authentication failures
- Connection errors
- Parsing errors
- Database errors

### Log Format

```python
logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=os.getenv("LOGGING", logging.INFO),
    datefmt="%Y-%m-%d %H:%M:%S"
)
```

**Example Output:**
```
2026-02-03 20:00:00.123 INFO     Worker SNP-192.168.90.23 websocket connected
2026-02-03 20:00:00.456 ERROR    Worker SNP-192.168.90.33 connection refused
```

---

## Development Notes

### Code Style

**Async/Await Everywhere:**
- All I/O operations are async
- Proper use of `async with` for context managers
- No blocking calls in main thread

**Error Handling Pattern:**
```python
try:
    # Operation
except SpecificError:
    # Handle specific case
except Exception as err:
    # Log and continue/retry
finally:
    # Cleanup resources
```

**Resource Management:**
- Always close sessions explicitly
- Use context managers where possible
- Cancel tasks before exit

### Testing Approach

**Manual Testing:**
```bash
# Start container
docker compose up -d

# Check logs
docker logs observe-snpexporter

# Test API
curl http://localhost:8080/api/connections

# Test metrics
curl http://localhost:8000/metrics/

# Test UI
open http://localhost:8080/
```

**Integration Testing:**
- Real SNP devices required
- WebSocket authentication tested
- Metric parsing validated with real data

---

## Future Enhancements

### Potential Features

1. **Authentication System**
   - User login for UI
   - API key authentication
   - RBAC (read-only vs admin)

2. **Enhanced Monitoring**
   - Connection uptime tracking
   - Message rate graphs
   - Error rate metrics

3. **Alerting Integration**
   - Built-in alerting rules
   - Email/Slack notifications
   - Threshold configuration UI

4. **Advanced Features**
   - Bulk operations (enable/disable multiple)
   - Connection groups/tags
   - Scheduled exports
   - Metric retention policies

5. **High Availability**
   - Multiple exporter instances
   - Shared database (PostgreSQL)
   - Leader election

---

## Troubleshooting Guide

### Common Issues

**Issue: Worker stuck in "connecting"**
- Check SNP device reachability
- Verify WebSocket URL format
- Check firewall rules

**Issue: Authentication failed (error status)**
- Verify username/password
- Check REST API URL
- Ensure SNP device is online

**Issue: No metrics appearing**
- Check subscription objectIds are valid
- Verify elementIP matches device
- Check logs for parsing errors

**Issue: Database locked**
- SQLite handles serialization automatically
- Increase poll_interval if frequent updates
- Check disk space

**Issue: High CPU usage**
- Reduce number of connections
- Increase INTERVAL value
- Check for excessive logging

### Debug Commands

```bash
# View real-time logs
docker logs -f observe-snpexporter

# Check database contents
docker exec observe-snpexporter sqlite3 /etc/snp_exporter/connections.db "SELECT * FROM snp_connections;"

# Check connection status
docker exec observe-snpexporter sqlite3 /etc/snp_exporter/connections.db "SELECT * FROM connection_status;"

# Test specific connection
curl -s http://localhost:8080/api/connections/1 | jq

# Trigger manual reload
curl http://localhost:8000/-/reload

# Export for backup
curl -s http://localhost:8080/api/export > backup.json
```

---

## Glossary

**SNP:** Signal Network Processor - Imagine Communications video processing device

**WebSocket:** Full-duplex communication protocol over TCP

**Prometheus:** Time-series database and monitoring system

**ASGI:** Asynchronous Server Gateway Interface (Python web standard)

**asyncio:** Python's built-in async I/O framework

**Info Metric:** Prometheus metric type for key-value metadata

**Gauge:** Prometheus metric type for values that can increase/decrease

**Counter:** Prometheus metric type for monotonically increasing values

**Element IP:** Internal IP address within SNP device (usually 127.0.0.1)

**Object ID:** Identifier for specific processing channels (e.g., "A-HD-1")

**Personality:** SNP processor configuration type (e.g., "Multiviewer", "Sync")

**ACO:** Automatic Changeover - SNP redundancy feature

**PTP:** Precision Time Protocol - Network time synchronization

---

## Contributing

### Code Modification Guidelines

1. **Adding New Metrics:**
   - Define Gauge/Counter/Info at module level
   - Update `parse_statuses()` with new status type
   - Add to README metrics documentation

2. **Adding New API Endpoints:**
   - Add route to `ui_app` or `app`
   - Update OpenAPI docs
   - Handle errors consistently

3. **Modifying Database:**
   - Update schema in `create_tables()`
   - Add migration logic if needed
   - Update CRUD functions

4. **Changing Worker Logic:**
   - Test with real SNP devices
   - Ensure proper error handling
   - Update logs appropriately

---

## License

(Add license information here)

## Support

For issues, questions, or contributions, please contact the development team.

---

**Document Version:** 1.0
**Last Updated:** 2026-02-03
**Python Version:** 3.14
**Docker Image:** snp_exporter:latest
