# SNP Exporter

A WebSocket Python docker container application. 
Subscribes to SNP statuses and serves HTTP Prometheus metrics with a web UI for connection management.

**Docker Hub:** `rivers1980/snp-metrics-exporter:0.1`

## Features

- **WebSocket Connection Management**: Connect to multiple SNP devices via WebSocket
- **Prometheus Metrics Export**: Expose hardware metrics for monitoring
- **Web UI**: Add, edit, and delete SNP connections through a web interface
- **Live Connection Status**: Monitor connection status in real-time
- **Config Reload**: Hot-reload configuration without restart

## Prerequisites

Ensure you have the following installed:

* Docker

## Getting Started

There are two ways to install and run the SNP Exporter:

### Option 1: Using Pre-Built Docker Image (Recommended)

Pull and run the pre-built image from Docker Hub:

```bash
# Create a directory for the database
mkdir -p /opt/snp_exporter

# Run the container
docker run -d \
  --name observe-snpexporter \
  -p 8000:8000 \
  -p 8080:8080 \
  -v /opt/snp_exporter:/etc/snp_exporter \
  -e LOGGING=INFO \
  -e INTERVAL=5 \
  -e POLL_INTERVAL=10 \
  rivers1980/snp-metrics-exporter:0.1
```

**Access the services:**
- **Web UI**: `http://host-ip:8080/` - Manage SNP connections
- **Metrics**: `http://host-ip:8000/metrics` - Prometheus metrics endpoint

**Using Docker Compose with pre-built image:**

Create a `docker-compose.yml` file:
```yaml
services:
  snp_exporter:
    image: rivers1980/snp-metrics-exporter:0.1
    container_name: observe-snpexporter
    hostname: observe-snpexporter
    ports:
      - "8000:8000"
      - "8080:8080"
    environment:
      - LOGGING=INFO
      - INTERVAL=5
      - POLL_INTERVAL=10
      - DB_PATH=/etc/snp_exporter/connections.db
    volumes:
      - ./data:/etc/snp_exporter/
```

Then run:
```bash
docker compose up -d
```

### Option 2: Building from Source

If you have the source code, you can build the image yourself:

1. **Unzip the files**:

```bash
unzip exporter_snp.zip -d /opt/snp_exporter
cd /opt/snp_exporter
```

2. **Build and start the container**:

```bash
docker compose up -d
```

3. **Access the services**:

Once running, you can access:
- **Web UI**: `http://host-ip:8080/` - Manage SNP connections
- **Metrics**: `http://host-ip:8000/metrics` - Prometheus metrics endpoint

## Web UI

The web interface allows you to:

### View Connections
- See all SNP connections with live status indicators:
  - 🟢 Connected - WebSocket connection active and receiving messages
  - 🔴 Disconnected - Connection lost, will retry
  - 🟡 Connecting - Establishing connection
  - ⚫ Error - Authentication failed or unrecoverable error
- View last update time for each connection
- Click "Metrics" button to view Prometheus metrics for a specific connection

### Add Connection
Click the "Add Connection" button and fill in:
- **Name**: Unique identifier for the connection
- **REST API URL**: Authentication endpoint (e.g., `https://192.168.1.1:9089/api/auth`)
- **WebSocket URL**: WebSocket endpoint (e.g., `wss://192.168.1.1/smm`)
- **Username/Password**: Authentication credentials
- **Object IDs**: Configure which data to subscribe to

#### Object IDs Configuration
Add subscriptions for the following object types:
- **ptp**: Precision Time Protocol status
- **system**: System hardware status (temperature, fans, alarms)
- **ipVidRx**: Video receiver status
- **procChannelHD**: HD channel status (requires Object ID)

### Edit Connection
Click the "Edit" button on any connection to modify its configuration. Changes are automatically applied when saved.

### Delete Connection
Click the "Delete" button to remove a connection. This will immediately disconnect the worker and remove all metrics.

### Export Configuration
Click the "Export" button to download all connections as a JSON file:
- Exports all connection configurations (including credentials)
- File is named with current date: `snp-connections-YYYY-MM-DD.json`
- Can be used for backup or migration
- Status and internal IDs are excluded from export

### Import Configuration
Click the "Import" button to restore connections from a previously exported JSON file:
- Supports JSON files exported from this application
- Existing connections with duplicate names are skipped
- Shows summary of imported/skipped connections
- Automatically triggers worker restart for imported connections
- **Note**: Import validates format and required fields before processing

### Reload Configuration
Click the "Reload Config" button to manually trigger a configuration reload:
- Forces immediate recheck of all connections from database
- Starts workers for new connections
- Stops workers for deleted/disabled connections
- Restarts workers with updated configuration
- Shows success notification when complete
- **Note**: Configuration reloads automatically every 10 seconds, so manual reload is only needed for immediate changes

### Metrics Link
Each connection has a "Metrics" button that opens the Prometheus metrics endpoint. Filter by target label:
```
ic_snp_api_status{target="connection_name"}
```

## Configuration

The application uses a SQLite database (`connections.db`) for persistent configuration. The database is automatically created on first startup.

### Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| **LOGGING** | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| **INTERVAL** | 5 | Message processing interval (seconds) |
| **POLL_INTERVAL** | 10 | Database poll interval for config changes (seconds) |
| **DB_PATH** | `/etc/snp_exporter/connections.db` | SQLite database file path |

## Common Commands

### When Using Pre-Built Image

| Task | Command |
| :--- | :--- |
| **View logs** | `docker logs observe-snpexporter` |
| **Stop container** | `docker stop observe-snpexporter` |
| **Remove container** | `docker rm observe-snpexporter` |
| **Pull latest image** | `docker pull rivers1980/snp-metrics-exporter:0.1` |
| **Update to latest** | `docker stop observe-snpexporter && docker rm observe-snpexporter && docker pull rivers1980/snp-metrics-exporter:0.1 && docker run -d --name observe-snpexporter -p 8000:8000 -p 8080:8080 -v /opt/snp_exporter:/etc/snp_exporter rivers1980/snp-metrics-exporter:0.1` |

### When Using Docker Compose

| Task | Command |
| :--- | :--- |
| **View logs** | `docker compose logs -f` |
| **Stop** container | `docker compose down` |
| **Restart** | `docker compose restart` |
| **Update image** | `docker compose pull && docker compose up -d` |
| **Remove** container image | `docker image rm snp_exporter` |

## API Endpoints

### Connection Management API (Port 8080)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/` | Web UI interface |
| GET | `/api/connections` | List all connections with status |
| GET | `/api/connections/{id}` | Get specific connection |
| POST | `/api/connections` | Add new connection |
| PUT | `/api/connections/{id}` | Update connection |
| DELETE | `/api/connections/{id}` | Delete connection |
| GET | `/api/export` | Export all connections as JSON |
| POST | `/api/import` | Import connections from JSON |

### Metrics API (Port 8000)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/metrics` | Prometheus metrics |
| GET | `/-/reload` | Trigger configuration reload |

## Prometheus Metrics

### Connection Metrics
- `ic_snp_api_status{target}` - Connection status (1=connected, 0=disconnected)
- `ic_snp_received_count{target}` - Total messages received
- `ic_snp_last_received_duration_seconds{target}` - Last message processing time

### System Metrics
- `ic_snp_mainboard_temperature{target}` - Main board temperature
- `ic_snp_ioboard_temperature{target}` - IO board temperature
- `ic_snp_powersupply_status{target}` - Power supply status (1=OK, 0=Not OK)
- `ic_snp_fpga_temperature{target,index}` - FPGA temperature
- `ic_snp_fpga_fan_status{target,index}` - FPGA fan status (1=OK, 0=Not OK)
- `ic_snp_front_fan_status{target,index}` - Front fan status (1=OK, 0=Not OK)
- `ic_snp_qsfp_temperature{target,index}` - QSFP temperature

### Alarm Metrics
- `ic_snp_major_alarms{target}` - Number of major alarms
- `ic_snp_minor_alarms{target}` - Number of minor alarms

### PTP Metrics
- `ic_snp_ptp_status{target}` - PTP status (1=Locked, 0=Not Locked)
- `ic_snp_ptp_master_offset{target}` - PTP master offset
- `ic_snp_ptp_master_delay{target}` - PTP master delay

### Video Metrics
- `ic_snp_video_rx{target,index}` - Video receiver information (info metric)

### Processor Metrics
- `ic_snp_processor_personality{target,processor}` - Processor personality for processorA, processorB, processorC, processorD (info metric)
  - Polled every 60 seconds via REST API
  - Examples: "Multiviewer", "Master Control Lite", "JPEG-XS Encoder (TR-07)", "Conv", "Sync", "Remap", "Dual Gateway"

## Architecture

The application runs two separate FastAPI servers:

1. **Metrics Server (Port 8000)**: Serves Prometheus metrics only
2. **UI Server (Port 8080)**: Web interface and management API

A worker task manages each connection:
- Establishes WebSocket connection
- Authenticates via REST API
- Subscribes to status updates
- Parses messages and updates Prometheus metrics
- Tracks connection status in database

Configuration changes are detected via periodic polling (default 10 seconds).
