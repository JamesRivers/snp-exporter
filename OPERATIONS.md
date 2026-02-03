# SNP Exporter - Operations Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Accessing the Web UI](#accessing-the-web-ui)
- [Adding Connections](#adding-connections)
- [Managing Connections](#managing-connections)
- [Export and Import](#export-and-import)
- [Monitoring with Prometheus](#monitoring-with-prometheus)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- Docker installed
- Network access to your SNP devices
- SNP device credentials (username and password)
- SNP device IP addresses

### Installation

**Docker Hub Image:** `rivers1980/snp-metrics-exporter:0.1`

Choose one of the following installation methods:

#### Method 1: Using Pre-Built Docker Image (Recommended)

**Fastest and easiest method - no source code required.**

1. **Create a directory for the database:**
   ```bash
   mkdir -p /opt/snp_exporter
   ```

2. **Pull and run the Docker image:**
   ```bash
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

3. **Verify the container is running:**
   ```bash
   docker ps | grep observe-snpexporter
   ```

   You should see:
   ```
   CONTAINER ID   IMAGE                                    STATUS        PORTS
   abc123def456   rivers1980/snp-metrics-exporter:0.1      Up 10 seconds 0.0.0.0:8000->8000/tcp, 0.0.0.0:8080->8080/tcp
   ```

4. **Check the application logs:**
   ```bash
   docker logs observe-snpexporter
   ```

   Successful startup shows:
   ```
   INFO     Database initialized
   INFO     Starting Uvicorn FastAPI metrics server on port 8000
   INFO     Starting Uvicorn FastAPI UI server on port 8080
   INFO     Starting reloader task
   ```

#### Method 2: Using Docker Compose with Pre-Built Image

**Best for production deployments with easier management.**

1. **Create a docker-compose.yml file:**
   ```bash
   mkdir -p /opt/snp_exporter
   cd /opt/snp_exporter
   ```

2. **Create docker-compose.yml with this content:**
   ```yaml
   services:
     snp_exporter:
       image: rivers1980/snp-metrics-exporter:0.1
       container_name: observe-snpexporter
       hostname: observe-snpexporter
       restart: unless-stopped
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

3. **Start the application:**
   ```bash
   docker compose up -d
   ```

4. **Verify:**
   ```bash
   docker compose ps
   docker compose logs
   ```

#### Method 3: Building from Source

**For developers or when customization is needed.**

1. **Extract the application files:**
   ```bash
   unzip exporter_snp.zip -d /opt/snp_exporter
   cd /opt/snp_exporter
   ```

2. **Build and start the container:**
   ```bash
   docker compose up -d
   ```

3. **Verify the container is running:**
   ```bash
   docker ps | grep observe-snpexporter
   ```

---

## Accessing the Web UI

### URLs

Once the application is running, you can access:

- **Web UI**: `http://{server-ip}:8080/`
  - Connection management interface
  - Real-time status monitoring
  - Configuration import/export

- **Metrics**: `http://{server-ip}:8000/metrics/`
  - Prometheus metrics endpoint
  - Used by Prometheus scraper

**Example:**
- If your server IP is `192.168.1.100`
- Web UI: `http://192.168.1.100:8080/`
- Metrics: `http://192.168.1.100:8000/metrics/`

### Web UI Overview

When you open the web UI, you'll see:

**Top Navigation Bar:**
- Application title: "SNP Exporter"
- Subtitle: "WebSocket Connection Manager"

**Action Buttons (Top Right):**
- **Export** (Green) - Download configuration backup
- **Import** (Cyan) - Restore configuration from file
- **Reload Config** (Gray) - Force configuration reload
- **Add Connection** (Blue) - Add new SNP connection

**Connection Table:**
- Lists all configured SNP connections
- Shows real-time status with color indicators
- Provides action buttons for each connection

**Status Indicators:**
- 🟢 **Connected** - WebSocket active, receiving data
- 🔴 **Disconnected** - Connection lost, will retry
- 🟡 **Connecting** - Establishing connection
- ⚫ **Error** - Authentication failed or unrecoverable error

---

## Adding Connections

### Step-by-Step Guide

#### Step 1: Click "Add Connection"

Click the blue "Add Connection" button in the top-right corner. A modal dialog will appear.

#### Step 2: Fill in Connection Details

##### Field 1: Name
**Description:** A unique identifier for this SNP connection. This name will appear in Prometheus metrics as the `target` label.

**Requirements:**
- Must be unique across all connections
- No special characters recommended (alphanumeric, hyphens, underscores)
- Case-sensitive

**Examples:**
- `SNP-Studio-A`
- `SNP-192.168.90.23`
- `MCR-Primary-SNP`
- `Production-SNP-01`

**Best Practice:** Use a naming convention that identifies the SNP device location or purpose.

---

##### Field 2: REST API URL
**Description:** The HTTPS endpoint used for authentication. This is where the exporter obtains the JWT token.

**Format:** `https://{device-ip}:{port}/api/auth`

**Standard Port:** `9089` (SNP default)

**Requirements:**
- Must start with `https://`
- Must include full path `/api/auth`
- Device must be network-accessible

**Examples:**
- `https://192.168.90.23:9089/api/auth`
- `https://10.50.1.100:9089/api/auth`
- `https://snp-studio-a.company.com:9089/api/auth`

**How to Find:**
- Check SNP device web interface URL
- Add `:9089/api/auth` to the IP address
- Example: If SNP web UI is at `https://192.168.90.23`, REST API is `https://192.168.90.23:9089/api/auth`

---

##### Field 3: WebSocket URL
**Description:** The WebSocket endpoint for real-time status updates. This is where the exporter receives monitoring data.

**Format:** `wss://{device-ip}/smm`

**Standard Path:** `/smm` (SNP Message Manager)

**Requirements:**
- Must start with `wss://` (secure WebSocket)
- Must end with `/smm`
- Same IP as REST API URL

**Examples:**
- `wss://192.168.90.23/smm`
- `wss://10.50.1.100/smm`
- `wss://snp-studio-a.company.com/smm`

**How to Find:**
- Use same IP/hostname as REST API
- Replace `https://` with `wss://`
- Remove port number, add `/smm` path
- Example: REST `https://192.168.90.23:9089/api/auth` → WebSocket `wss://192.168.90.23/smm`

---

##### Field 4: Username
**Description:** SNP device login username for authentication.

**Requirements:**
- Must have read access to SNP device
- Case-sensitive
- No special permissions required beyond basic read access

**Common Defaults:**
- `admin`
- `operator`
- `monitor`

**Examples:**
- `admin`
- `prometheus-exporter`
- `readonly-user`

**Best Practice:** Create a dedicated monitoring user on the SNP device with read-only access.

---

##### Field 5: Password
**Description:** Password for the SNP device username.

**Requirements:**
- Stored in plaintext in database
- Case-sensitive
- Special characters supported

**Security Note:** The password is visible in the UI and stored unencrypted. Ensure your exporter server is secured appropriately.

**Examples:**
- `password` (default for many SNP devices)
- `Monitor123!`
- `$ecur3P@ss`

**Best Practice:** Use a strong password and rotate regularly.

---

##### Field 6: Enabled Checkbox
**Description:** Whether this connection should be active.

**Options:**
- ✓ **Checked (Enabled)** - Worker will connect to SNP device
- ☐ **Unchecked (Disabled)** - Connection stored but inactive

**Use Cases:**
- Disable temporarily during SNP maintenance
- Keep configuration but stop monitoring
- Test new connection before enabling

**Default:** Checked (enabled)

---

#### Step 3: Configure Object ID Subscriptions

This section defines what data to monitor from the SNP device.

##### Object Type Dropdown
**Description:** Select the type of SNP object to monitor.

**Options:**

**1. ptp (Precision Time Protocol)**
- Monitors timing and synchronization
- No Object ID required
- Metrics: PTP status, master offset, master delay

**2. system (System Status)**
- Monitors hardware health
- No Object ID required
- Metrics: Temperatures, fans, power supply, alarms, FPGA stats

**3. ipVidRx (IP Video Receiver)**
- Monitors video receiver inputs
- No Object ID required
- Metrics: Video standard, colorimetry

**4. procChannelHD (Processing Channel HD)**
- Monitors specific processing channels
- **Requires Object ID** (e.g., "A-HD-1")
- Metrics: ACO A/B status

##### Element IP Field
**Description:** Internal SNP element IP address.

**Default:** `127.0.0.1` (recommended for most cases)

**What it means:** The SNP device uses this to route messages internally. For standard monitoring, always use `127.0.0.1`.

**When to change:** Only if instructed by SNP device documentation or support.

**Examples:**
- `127.0.0.1` (standard, use this)
- `192.168.90.23` (specific routing scenarios)

##### Object ID Field
**Description:** Specific processing channel identifier. Only visible when "procChannelHD" is selected.

**Format:** `{Processor}-HD-{Number}`

**Components:**
- `Processor`: A, B, C, or D (SNP processor)
- `Number`: 1-16 (channel number)

**Examples:**
- `A-HD-1` (Processor A, Channel 1)
- `B-HD-8` (Processor B, Channel 8)
- `C-HD-12` (Processor C, Channel 12)
- `D-HD-16` (Processor D, Channel 16)

**How to find available channels:**
- Check SNP device web interface
- Look at channel names in device configuration
- Typically ranges from 1 to 16 per processor

##### Adding Multiple Objects

To monitor multiple aspects of an SNP device:

1. Configure first object (e.g., "ptp")
2. Click "Add Object ID" button
3. Configure second object (e.g., "system")
4. Click "Add Object ID" button
5. Continue for all objects you want to monitor

**Recommended Set:**
```
Object Type: ptp          Element IP: 127.0.0.1  Object ID: (none)
Object Type: system       Element IP: 127.0.0.1  Object ID: (none)
Object Type: ipVidRx      Element IP: 127.0.0.1  Object ID: (none)
Object Type: procChannelHD Element IP: 127.0.0.1  Object ID: A-HD-1
```

##### Objects Table
Shows all added object subscriptions. Each row displays:
- Object Type
- Element IP
- Object ID (if applicable)
- Remove button (red)

Click "Remove" to delete an object from the subscription list.

##### JSON Preview
Shows the final subscription array that will be sent to the SNP device. This is automatically updated as you add/remove objects.

**Example Preview:**
```json
[
  {
    "elementIP": "127.0.0.1",
    "objectType": "ptp"
  },
  {
    "elementIP": "127.0.0.1",
    "objectType": "system"
  },
  {
    "elementIP": "127.0.0.1",
    "objectType": "ipVidRx"
  },
  {
    "elementIP": "127.0.0.1",
    "objectType": "procChannelHD",
    "objectId": "A-HD-1"
  }
]
```

#### Step 4: Save the Connection

Click the blue "Save" button at the bottom of the modal.

**What happens:**
1. Form is validated (all required fields must be filled)
2. Connection is saved to database
3. Configuration reload is triggered automatically
4. Green success notification appears: "Config Reloaded! Workers are restarting..."
5. Modal closes
6. New connection appears in the table
7. Within 10 seconds, worker starts connecting
8. Status changes from "disconnected" → "connecting" → "connected"

**If save fails:**
- Check that connection name is unique
- Verify at least one object ID was added
- Check browser console for errors

---

### Complete Example: Adding a Production SNP

**Scenario:** You want to monitor SNP device at `192.168.90.23` in your studio.

**Step-by-Step:**

1. Click "Add Connection"

2. Fill in the form:
   - **Name:** `Studio-A-SNP`
   - **REST API URL:** `https://192.168.90.23:9089/api/auth`
   - **WebSocket URL:** `wss://192.168.90.23/smm`
   - **Username:** `admin`
   - **Password:** `password`
   - **Enabled:** ✓ (checked)

3. Add object subscriptions:
   
   **First object (PTP timing):**
   - Object Type: `ptp`
   - Element IP: `127.0.0.1`
   - Click "Add Object ID"
   
   **Second object (System health):**
   - Object Type: `system`
   - Element IP: `127.0.0.1`
   - Click "Add Object ID"
   
   **Third object (Video receiver):**
   - Object Type: `ipVidRx`
   - Element IP: `127.0.0.1`
   - Click "Add Object ID"
   
   **Fourth object (Processing channel):**
   - Object Type: `procChannelHD`
   - Element IP: `127.0.0.1`
   - Object ID: `A-HD-1`
   - Click "Add Object ID"

4. Verify JSON Preview shows:
   ```json
   [
     {
       "elementIP": "127.0.0.1",
       "objectType": "ptp"
     },
     {
       "elementIP": "127.0.0.1",
       "objectType": "system"
     },
     {
       "elementIP": "127.0.0.1",
       "objectType": "ipVidRx"
     },
     {
       "elementIP": "127.0.0.1",
       "objectType": "procChannelHD",
       "objectId": "A-HD-1"
     }
   ]
   ```

5. Click "Save"

6. Wait 5-10 seconds and verify:
   - Connection appears in table
   - Status shows 🟡 Connecting, then 🟢 Connected
   - Last Update timestamp shows recent time

7. Click "Metrics" button to view Prometheus data

**Expected Result:**
Your SNP device is now being monitored. Metrics are available at `http://server:8000/metrics/` with `target="Studio-A-SNP"` label.

---

## Managing Connections

### Viewing Connection Status

The main table displays all connections with:

**Columns:**
- **ID** - Unique database identifier
- **Name** - Your custom connection name
- **WebSocket URL** - The wss:// endpoint
- **Status** - Current connection state with icon
- **Last Update** - Timestamp of last received message
- **Actions** - Buttons for managing the connection

**Status Colors:**
- 🟢 Green (Connected) - Everything working
- 🔴 Red (Disconnected) - Will retry automatically
- 🟡 Yellow (Connecting) - Connection in progress
- ⚫ Black (Error) - Fix configuration

**Auto-Refresh:**
The table updates every 5 seconds automatically. No need to refresh the page.

---

### Editing a Connection

**When to edit:**
- Change SNP device IP address
- Update credentials
- Modify object subscriptions
- Enable/disable connection
- Correct configuration errors

**Steps:**

1. Click the yellow "Edit" button for the connection you want to modify

2. The Add/Edit modal opens with pre-filled data

3. Modify any fields:
   - Change name (must remain unique)
   - Update URLs if device IP changed
   - Update credentials if password changed
   - Add/remove object subscriptions
   - Check/uncheck Enabled

4. Click "Save"

**What happens:**
- Connection is updated in database
- Reload is triggered automatically
- Worker is restarted with new configuration
- Green notification appears
- New configuration takes effect within 10 seconds

**Important Notes:**
- Changing the name restarts the worker
- Changing objects_ids triggers resubscription
- Disabling sets enabled=false, stops worker immediately

---

### Deleting a Connection

**When to delete:**
- SNP device decommissioned
- Connection no longer needed
- Duplicate connection created by mistake

**Steps:**

1. Click the red "Delete" button for the connection

2. Confirmation dialog appears:
   ```
   Are you sure you want to delete this connection?
   [Cancel] [Delete]
   ```

3. Click red "Delete" button to confirm

**What happens:**
- Connection removed from database
- Worker is cancelled immediately
- WebSocket connection closed
- Prometheus metrics removed for this target
- Green notification appears
- Connection disappears from table

**Important Notes:**
- **This action cannot be undone** (unless you have an export backup)
- All historical metrics for this target are removed
- Prometheus will show no more data for this `target` label

**Recovery:**
If deleted by mistake:
1. Use Export/Import to restore from backup
2. Or manually re-add the connection with same details

---

### Viewing Metrics

Each connection has a "Metrics" button that opens the Prometheus endpoint in a new tab.

**Steps:**

1. Find your connection in the table
2. Click the cyan "Metrics" button in the Actions column
3. New browser tab opens to `http://server:8000/metrics/`
4. Metrics are displayed in Prometheus text format

**Finding your connection's metrics:**
Search for your connection name in the metrics output:
```
# Example: Find metrics for "Studio-A-SNP"
ic_snp_api_status{target="Studio-A-SNP"} 1.0
ic_snp_mainboard_temperature{target="Studio-A-SNP"} 49.0
ic_snp_ptp_status{target="Studio-A-SNP"} 1.0
```

**Metric Browser:**
Use browser search (Ctrl+F / Cmd+F) to find specific metrics:
- Search `target="Studio-A-SNP"` to see all metrics for that connection
- Search `temperature` to see all temperature metrics
- Search `alarm` to see alarm counts

---

### Enabling and Disabling Connections

**Enable/Disable via Edit:**

1. Click "Edit" on the connection
2. Check or uncheck the "Enabled" checkbox
3. Click "Save"

**When Enabled (Checked):**
- Worker connects to SNP device
- Metrics are collected and exposed
- Connection status shows in table

**When Disabled (Unchecked):**
- Worker stops immediately
- WebSocket disconnects
- Metrics stop updating (last values retained)
- Status shows as "disconnected"
- Configuration remains in database

**Use Cases:**
- **Temporarily disable** during SNP maintenance
- **Disable** faulty connections while troubleshooting
- **Keep configuration** but stop monitoring

---

## Export and Import

### Export Configuration

**Purpose:** Create a backup of all connection configurations for disaster recovery, migration, or documentation.

#### How to Export

1. Click the green "Export" button in the top-right corner

2. Your browser automatically downloads a JSON file named:
   ```
   snp-connections-YYYY-MM-DD.json
   ```
   Example: `snp-connections-2026-02-03.json`

3. A blue notification appears:
   ```
   Import Complete! Exported 5 connection(s) successfully.
   ```

#### What Gets Exported

**Included:**
- Connection name
- REST API URL
- WebSocket URL
- Username
- Password (plaintext)
- Object subscriptions
- Enabled status

**Excluded:**
- Database IDs (auto-generated on import)
- Connection status (real-time data)
- Created/Updated timestamps

#### Export File Format

```json
{
  "version": "1.0",
  "exported_at": "2026-02-03 20:30:00",
  "connections": [
    {
      "name": "Studio-A-SNP",
      "restapi": "https://192.168.90.23:9089/api/auth",
      "websocket": "wss://192.168.90.23/smm",
      "username": "admin",
      "password": "password",
      "objects_ids": [
        {
          "elementIP": "127.0.0.1",
          "objectType": "ptp"
        },
        {
          "elementIP": "127.0.0.1",
          "objectType": "system"
        }
      ],
      "enabled": true
    },
    {
      "name": "Studio-B-SNP",
      "restapi": "https://192.168.90.33:9089/api/auth",
      "websocket": "wss://192.168.90.33/smm",
      "username": "admin",
      "password": "password",
      "objects_ids": [
        {
          "elementIP": "127.0.0.1",
          "objectType": "system"
        }
      ],
      "enabled": true
    }
  ]
}
```

#### Export Use Cases

**1. Regular Backups**
- Export daily/weekly
- Store in secure location
- Quick recovery if database corrupted

**2. Migration**
- Export from old server
- Import on new server
- All connections transferred instantly

**3. Documentation**
- Human-readable JSON format
- Shows all configured connections
- Can be versioned in Git

**4. Bulk Editing**
- Export to file
- Edit JSON with text editor
- Import modified configuration

**5. Disaster Recovery**
- Keep export files off-server
- Restore after hardware failure
- Minimize downtime

---

### Import Configuration

**Purpose:** Restore connections from a previously exported JSON file, or bulk-add multiple connections at once.

#### How to Import

1. Click the cyan "Import" button in the top-right corner

2. File picker dialog opens (only .json files shown)

3. Select your previously exported JSON file

4. Confirmation dialog appears:
   ```
   Import 5 connection(s)?
   
   Existing connections with the same name will be skipped.
   
   [Cancel] [OK]
   ```

5. Click "OK" to proceed

6. Import processes with validation:
   - Checks JSON format
   - Validates required fields
   - Checks for duplicate names
   - Inserts new connections
   - Triggers configuration reload

7. Blue notification appears with summary:
   ```
   Import Complete! Imported: 3, Skipped: 2
   ```

8. Connection table refreshes with new connections

9. Workers start automatically for imported connections

#### Import Validation

**Required Fields:**
Every connection in the import file must have:
- `name` (string, unique)
- `restapi` (string, URL)
- `websocket` (string, URL)
- `username` (string)
- `password` (string)
- `objects_ids` (array, non-empty)

**Optional Fields:**
- `enabled` (boolean, defaults to true)

**Validation Rules:**
1. **Duplicate Names:** Skipped with notification
2. **Missing Fields:** Skipped with error message
3. **Invalid Format:** Entire import rejected

#### Import Behavior

**Duplicate Handling:**
Connections with existing names are **skipped** to prevent data loss.

**Example:**
```
Database has: "Studio-A-SNP"
Import file has: "Studio-A-SNP", "Studio-B-SNP"

Result:
- "Studio-A-SNP" → Skipped (already exists)
- "Studio-B-SNP" → Imported successfully

Notification: "Imported: 1, Skipped: 1"
```

**To update existing connection:**
1. Delete the old connection first
2. Then import the new configuration
3. Or use Edit instead of Import

#### Viewing Import Errors

If connections are skipped, check the browser console:

1. Press F12 (Chrome/Firefox) to open Developer Tools
2. Click "Console" tab
3. Look for import error messages:
   ```
   Import errors: [
     "Connection 'Studio-A-SNP' already exists, skipped",
     "Connection 'Bad-Config' missing required fields"
   ]
   ```

#### Import Use Cases

**1. Restore from Backup**
```
Scenario: Database corrupted or accidentally deleted
Steps:
  1. Export file available: snp-connections-2026-02-03.json
  2. Click Import
  3. Select backup file
  4. Confirm import
  5. All connections restored
```

**2. Migrate to New Server**
```
Scenario: Moving exporter to new hardware
Steps:
  1. Old server: Export configuration
  2. Copy JSON file to new server
  3. New server: Import configuration
  4. All connections active on new server
```

**3. Bulk Configuration**
```
Scenario: Adding 20 SNP devices at once
Steps:
  1. Create JSON file manually or via script
  2. Follow export file format
  3. Import file with all 20 connections
  4. Faster than adding one-by-one via UI
```

**4. Environment Cloning**
```
Scenario: Replicate production config in staging
Steps:
  1. Production: Export configuration
  2. Edit JSON: Change IP addresses for staging
  3. Staging: Import modified file
  4. Same connections, different endpoints
```

---

### Manual Reload Configuration

**Purpose:** Force immediate configuration check without waiting for automatic 10-second polling.

#### When to Use

- After adding/editing/deleting connection (optional, auto-reload works)
- To verify configuration changes applied
- Troubleshooting connection issues
- Forcing worker restart

#### How to Reload

1. Click the gray "Reload Config" button (circular arrow icon)

2. Green notification appears:
   ```
   Config Reloaded! Workers are restarting with new configuration.
   ```

3. Check logs to verify:
   ```bash
   docker logs observe-snpexporter | tail -20
   ```

**What happens:**
- Reloader wakes immediately
- Queries database for enabled connections
- Compares with running workers
- Starts/stops/restarts workers as needed

**Note:** Configuration reloads automatically every 10 seconds, so manual reload is usually unnecessary.

---

## Monitoring with Prometheus

### Configuring Prometheus

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'snp_exporter'
    static_configs:
      - targets: ['192.168.1.100:8000']  # Replace with your exporter server IP
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Scrape Interval Recommendation:** 30-60 seconds (SNP data doesn't change rapidly)

### Available Metrics

#### Connection Metrics
```prometheus
ic_snp_api_status{target="Studio-A-SNP"} 1.0
ic_snp_received_count_total{target="Studio-A-SNP"} 1234.0
ic_snp_last_received_duration_seconds{target="Studio-A-SNP"} 0.002
```

**Usage:**
- `api_status`: 1 = connected, 0 = disconnected
- `received_count`: Total messages received (counter)
- `received_duration`: Last message processing time

**Alert Example:**
```yaml
- alert: SNPDisconnected
  expr: ic_snp_api_status == 0
  for: 5m
  annotations:
    summary: "SNP {{ $labels.target }} disconnected"
```

#### Temperature Metrics
```prometheus
ic_snp_mainboard_temperature{target="Studio-A-SNP"} 49.0
ic_snp_ioboard_temperature{target="Studio-A-SNP"} 43.0
ic_snp_fpga_temperature{target="Studio-A-SNP",index="0"} 65.0
ic_snp_qsfp_temperature{target="Studio-A-SNP",index="1"} 52.0
```

**Alert Example:**
```yaml
- alert: SNPHighTemperature
  expr: ic_snp_mainboard_temperature > 70
  annotations:
    summary: "SNP {{ $labels.target }} temperature critical"
```

#### Hardware Status Metrics
```prometheus
ic_snp_powersupply_status{target="Studio-A-SNP"} 1.0
ic_snp_fpga_fan_status{target="Studio-A-SNP",index="0"} 1.0
ic_snp_front_fan_status{target="Studio-A-SNP",index="0"} 1.0
```

**Values:** 1 = OK, 0 = Not OK

**Alert Example:**
```yaml
- alert: SNPFanFailure
  expr: ic_snp_front_fan_status == 0
  annotations:
    summary: "SNP {{ $labels.target }} fan {{ $labels.index }} failed"
```

#### Alarm Metrics
```prometheus
ic_snp_major_alarms{target="Studio-A-SNP"} 0.0
ic_snp_minor_alarms{target="Studio-A-SNP"} 2.0
```

**Alert Example:**
```yaml
- alert: SNPMajorAlarm
  expr: ic_snp_major_alarms > 0
  annotations:
    summary: "SNP {{ $labels.target }} has {{ $value }} major alarms"
```

#### PTP Metrics

**Status Metrics:**
```prometheus
ic_snp_ptp_status{target="Studio-A-SNP"} 1.0
ic_snp_ptp_master_offset{target="Studio-A-SNP"} 0.642
ic_snp_ptp_master_delay{target="Studio-A-SNP"} 0.169
ic_snp_ptp_is_master{target="Studio-A-SNP"} 0.0
ic_snp_ptp_biggest_sys_time_update_ms{target="Studio-A-SNP"} 1004.0
ic_snp_ptp_num_sys_time_updates{target="Studio-A-SNP"} 23.0
```

**Information Metric:**
```prometheus
ic_snp_ptp_info{
  target="Studio-A-SNP",
  clock_identity="00 90 F9 FF FE 34 6C AF",
  controller_state="Locked",
  master_ip="2.2.2.2",
  master_interface_ip="192.168.61.33",
  master_uuid="00-04-B3-FF-FE-F0-14-7D",
  master_present="Primary/Secondary",
  utc_time="Tue Feb 3 22:04:15 2026",
  rtc_time="N/A"
} 1.0
```

**Metric Descriptions:**
- `ptp_status`: 1 = Locked, 0 = Not Locked
- `ptp_master_offset`: Offset from master (microseconds)
- `ptp_master_delay`: Delay to master (microseconds)
- `ptp_is_master`: 1 = Master, 0 = Slave
- `ptp_biggest_sys_time_update_ms`: Largest time correction (milliseconds)
- `ptp_num_sys_time_updates`: Count of time corrections
- `ptp_info`: Detailed PTP information including master IP, clock ID, UTC time

**Alert Examples:**
```yaml
# PTP Not Locked
- alert: SNPPTPUnlocked
  expr: ic_snp_ptp_status == 0
  for: 2m
  annotations:
    summary: "SNP {{ $labels.target }} PTP not locked"

# Large Time Adjustment
- alert: SNPPTPLargeTimeUpdate
  expr: ic_snp_ptp_biggest_sys_time_update_ms > 500
  annotations:
    summary: "SNP {{ $labels.target }} had large time update: {{ $value }}ms"

# PTP Master Changed
- alert: SNPPTPMasterChanged
  expr: changes(ic_snp_ptp_info[5m]) > 0
  annotations:
    summary: "SNP {{ $labels.target }} PTP master changed"
```

#### Video Receiver Metrics
```prometheus
ic_snp_video_rx_info{target="Studio-A-SNP",index="0",video="1080i/59.94",colorimetry="BT.709"} 1.0
```

**Info Metric:** Contains labels with video standard and colorimetry information.

#### Processor Personality Metrics
```prometheus
ic_snp_processor_personality_info{target="Studio-A-SNP",processor="processorA",personality="Multiviewer"} 1.0
ic_snp_processor_personality_info{target="Studio-A-SNP",processor="processorB",personality="Master Control Lite"} 1.0
ic_snp_processor_personality_info{target="Studio-A-SNP",processor="processorC",personality="Remap"} 1.0
ic_snp_processor_personality_info{target="Studio-A-SNP",processor="processorD",personality="Dual Gateway"} 1.0
```

**Info Metric:** Shows what each processor is configured to do.

**Query Example:**
```promql
# List all processor personalities
ic_snp_processor_personality_info
```

---

## Troubleshooting

### Connection Status Shows "Error"

**Possible Causes:**
1. **Incorrect credentials**
   - Verify username and password
   - Check for typos
   - Try logging into SNP web interface with same credentials

2. **Wrong REST API URL**
   - Verify format: `https://{ip}:9089/api/auth`
   - Check IP address is correct
   - Ensure port 9089 is accessible

3. **Network connectivity**
   - Ping the SNP device from exporter server
   - Check firewall rules
   - Verify SNP device is powered on

**How to Fix:**
1. Click "Edit" on the connection
2. Verify all fields are correct
3. Test SNP web interface login manually
4. Click "Save"
5. Status should change to "connecting" then "connected"

---

### Connection Status Shows "Disconnected"

**Meaning:** Connection was working but lost. Exporter will retry automatically.

**Possible Causes:**
1. **Temporary network issue**
   - Wait 15-30 seconds
   - Should reconnect automatically

2. **SNP device rebooting**
   - Check SNP device status
   - Connection restores when device is back online

3. **WebSocket URL incorrect**
   - Edit connection
   - Verify WebSocket URL: `wss://{ip}/smm`

**Normal Behavior:**
- Brief disconnections are normal
- Exporter retries every 15 seconds
- No action required unless persistent

---

### Connection Status Shows "Connecting" Forever

**Possible Causes:**
1. **SNP device not responding**
   - Check device is online
   - Verify network path

2. **WebSocket port blocked**
   - Check firewall allows WSS (port 443 typically)
   - Test with: `telnet {snp-ip} 443`

3. **SSL certificate issue**
   - Normally handled by exporter
   - Check logs for SSL errors

**How to Fix:**
1. Check docker logs:
   ```bash
   docker logs observe-snpexporter | grep "Studio-A-SNP"
   ```
2. Look for specific error messages
3. Fix underlying issue
4. Connection retries automatically

---

### No Metrics Appearing in Prometheus

**Checklist:**

1. **Verify connection is "connected"**
   - Check web UI status
   - Should show 🟢 green

2. **Check metrics endpoint**
   ```bash
   curl http://localhost:8000/metrics/ | grep ic_snp
   ```
   Should return metrics

3. **Verify Prometheus scraping**
   - Check Prometheus targets page
   - Should show SNP exporter as "UP"
   - Check for scrape errors

4. **Check object subscriptions**
   - Edit connection
   - Verify objects_ids has at least one entry
   - Save if empty

5. **Check logs for parsing errors**
   ```bash
   docker logs observe-snpexporter | grep ERROR
   ```

---

### Import Failed

**Error: "Invalid import file format"**
- Ensure JSON file has "connections" key
- Validate JSON syntax: `cat file.json | jq`
- Use exported file as template

**Error: Connections skipped**
- Check for duplicate names
- Review errors in browser console
- Fix JSON structure issues

**Error: "Failed to import"**
- Check file is valid JSON
- Ensure all required fields present
- Review API error in console

---

### Worker Keeps Restarting

**Symptoms:**
- Status alternates between connecting/connected/disconnected
- Logs show repeated connection attempts

**Possible Causes:**

1. **Object subscriptions invalid**
   - Check objectId is correct
   - Verify objectType is valid
   - Use correct elementIP

2. **SNP device unstable**
   - Check SNP device health
   - Review SNP device logs
   - Contact device administrator

3. **Network path unstable**
   - Check network connectivity
   - Look for packet loss
   - Verify no intermittent firewall blocking

**How to Diagnose:**
```bash
# Watch logs in real-time
docker logs -f observe-snpexporter

# Look for pattern
grep "Worker Studio-A-SNP" logs.txt

# Check message types received
grep "received message type" logs.txt
```

---

### Database Issues

**Error: "Database locked"**
- Rare with current implementation
- SQLite handles concurrent access
- If persistent, restart container:
  ```bash
  docker compose restart
  ```

**Corrupt Database:**
```bash
# Backup database
docker exec observe-snpexporter cp /etc/snp_exporter/connections.db /etc/snp_exporter/connections.db.bak

# Check integrity
docker exec observe-snpexporter sqlite3 /etc/snp_exporter/connections.db "PRAGMA integrity_check;"

# If corrupt, restore from export
# Delete database and import from JSON file
```

---

## Operational Best Practices

### Daily Operations

1. **Check Dashboard**
   - Open web UI daily
   - Verify all connections show 🟢 green
   - Review any error status connections

2. **Monitor Metrics**
   - Configure Grafana dashboards
   - Set up alerts for critical metrics
   - Review alarm counts regularly

3. **Export Backups**
   - Export configuration weekly
   - Store in version control (Git)
   - Keep off-server backup

### Adding New SNP Devices

**Checklist:**
- [ ] Obtain SNP device IP address
- [ ] Get authentication credentials
- [ ] Test SNP web interface login
- [ ] Decide on connection name
- [ ] Determine which objects to monitor
- [ ] Add connection via web UI
- [ ] Verify status shows "connected"
- [ ] Check metrics endpoint
- [ ] Add to Prometheus scrape config
- [ ] Create Grafana dashboards
- [ ] Export backup with new connection

### Maintenance Windows

**Before SNP Maintenance:**
1. Export current configuration (backup)
2. Optionally disable connection (prevents error alerts)
3. Note start time

**During SNP Maintenance:**
- Connection shows "disconnected" (normal)
- No action required

**After SNP Maintenance:**
1. Re-enable connection if disabled
2. Verify status returns to "connected"
3. Check metrics are updating
4. Verify processor personalities didn't change

### Upgrading the Exporter

```bash
# 1. Export current configuration
curl http://localhost:8080/api/export > backup-$(date +%Y%m%d).json

# 2. Stop container
docker compose down

# 3. Backup database
cp connections.db connections.db.backup

# 4. Update code/image
git pull  # or unzip new version

# 5. Rebuild
docker compose build

# 6. Start
docker compose up -d

# 7. Verify
docker logs observe-snpexporter
curl http://localhost:8080/api/connections

# 8. If issues, rollback:
docker compose down
# Restore old version and database
docker compose up -d
```

---

## Quick Reference

### Common Tasks

| Task | Steps |
|------|-------|
| **Add Connection** | Click "Add Connection" → Fill form → Save |
| **Edit Connection** | Click "Edit" → Modify fields → Save |
| **Delete Connection** | Click "Delete" → Confirm |
| **Export Config** | Click "Export" → File downloads |
| **Import Config** | Click "Import" → Select file → Confirm |
| **Manual Reload** | Click "Reload Config" |
| **View Metrics** | Click "Metrics" button on connection row |
| **Check Status** | View table, auto-refreshes every 5s |
| **View Logs** | `docker logs observe-snpexporter` |

### Field Quick Reference

| Field | Example Value | Required | Notes |
|-------|---------------|----------|-------|
| Name | `Studio-A-SNP` | Yes | Unique identifier |
| REST API URL | `https://192.168.90.23:9089/api/auth` | Yes | For authentication |
| WebSocket URL | `wss://192.168.90.23/smm` | Yes | For status updates |
| Username | `admin` | Yes | SNP login |
| Password | `password` | Yes | SNP password |
| Enabled | ✓ | No | Default: checked |
| Object Type | `ptp`, `system`, `ipVidRx`, `procChannelHD` | Yes | What to monitor |
| Element IP | `127.0.0.1` | Yes | Default: 127.0.0.1 |
| Object ID | `A-HD-1` | Only for procChannelHD | Channel identifier |

### Status Meanings

| Icon | Status | Meaning | Action |
|------|--------|---------|--------|
| 🟢 | Connected | Working normally | None |
| 🔴 | Disconnected | Temporary issue, retrying | Wait or check device |
| 🟡 | Connecting | Initial connection | Wait 10-30 seconds |
| ⚫ | Error | Configuration problem | Edit and fix |

---

## Advanced Operations

### Editing JSON Export Files

Export files can be edited manually for bulk operations:

1. **Export configuration:**
   ```bash
   curl http://localhost:8080/api/export > config.json
   ```

2. **Edit with text editor:**
   ```bash
   nano config.json
   ```

3. **Modify connections:**
   - Add new connections to array
   - Update IP addresses
   - Change credentials
   - Modify object subscriptions

4. **Validate JSON:**
   ```bash
   cat config.json | jq . > /dev/null && echo "Valid" || echo "Invalid"
   ```

5. **Import modified file:**
   - Use web UI Import button
   - Or via API:
     ```bash
     curl -X POST http://localhost:8080/api/import \
       -H "Content-Type: application/json" \
       -d @config.json
     ```

### Bulk Operations via API

**Add multiple connections via script:**
```bash
#!/bin/bash

for ip in 192.168.90.{23,33,43,53}; do
  curl -X POST http://localhost:8080/api/connections \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"SNP-${ip}\",
      \"restapi\": \"https://${ip}:9089/api/auth\",
      \"websocket\": \"wss://${ip}/smm\",
      \"username\": \"admin\",
      \"password\": \"password\",
      \"objects_ids\": [
        {\"elementIP\": \"127.0.0.1\", \"objectType\": \"ptp\"},
        {\"elementIP\": \"127.0.0.1\", \"objectType\": \"system\"}
      ],
      \"enabled\": true
    }"
done
```

**Disable all connections:**
```bash
#!/bin/bash

# Get all connection IDs
ids=$(curl -s http://localhost:8080/api/connections | jq -r '.[].id')

# Disable each one
for id in $ids; do
  curl -X PUT http://localhost:8080/api/connections/$id \
    -H "Content-Type: application/json" \
    -d "{\"enabled\": false}"
done
```

### Monitoring the Exporter Itself

**Check container health:**
```bash
docker ps --filter name=observe-snpexporter
docker stats observe-snpexporter
```

**Check database size:**
```bash
docker exec observe-snpexporter ls -lh /etc/snp_exporter/connections.db
```

**Check active connections:**
```bash
docker exec observe-snpexporter ss -tn | grep 443
```

**Memory usage:**
```bash
docker exec observe-snpexporter ps aux
```

---

## Workflow Examples

### Scenario 1: New SNP Device Deployed

**Context:** New SNP device installed at 192.168.90.50, you need to start monitoring it.

**Workflow:**

1. **Gather Information:**
   - Device IP: `192.168.90.50`
   - Username: `admin`
   - Password: `Monitor2026!`
   - Location: Control Room B

2. **Add Connection:**
   - Name: `ControlRoom-B-SNP`
   - REST API: `https://192.168.90.50:9089/api/auth`
   - WebSocket: `wss://192.168.90.50/smm`
   - Username: `admin`
   - Password: `Monitor2026!`

3. **Configure Monitoring:**
   - Add object: `ptp` (timing critical)
   - Add object: `system` (hardware health)
   - Add object: `ipVidRx` (video inputs)

4. **Verify:**
   - Click "Save"
   - Wait 10 seconds
   - Check status is 🟢 Connected
   - Click "Metrics" to see data
   - Add to Prometheus config
   - Create Grafana dashboard

5. **Document:**
   - Export configuration
   - Update network documentation
   - Inform team

---

### Scenario 2: SNP Device IP Address Changed

**Context:** SNP device IP changed from 192.168.90.23 to 192.168.90.100 due to network reconfiguration.

**Workflow:**

1. **Identify Connection:**
   - Find connection in table (e.g., "Studio-A-SNP")
   - Note current configuration

2. **Edit Connection:**
   - Click "Edit" button
   - Update REST API URL: `https://192.168.90.100:9089/api/auth`
   - Update WebSocket URL: `wss://192.168.90.100/smm`
   - Keep all other fields same
   - Click "Save"

3. **Verify:**
   - Status should change: disconnected → connecting → connected
   - Check logs for successful authentication
   - Verify metrics updating

4. **Result:**
   - Same connection name (Prometheus graphs unaffected)
   - New IP address
   - Historical metrics preserved

---

### Scenario 3: Migrating to New Exporter Server

**Context:** Moving exporter from old server (192.168.1.50) to new server (192.168.1.100).

**Workflow:**

**On Old Server:**
1. Export configuration:
   - Click "Export" button
   - Save file: `snp-connections-backup.json`
   - Copy file to new server

**On New Server:**
2. Install exporter:
   ```bash
   unzip exporter_snp.zip -d /opt/snp_exporter
   cd /opt/snp_exporter
   docker compose up -d
   ```

3. Import configuration:
   - Open web UI: `http://192.168.1.100:8080/`
   - Click "Import" button
   - Select `snp-connections-backup.json`
   - Confirm import

4. Verify all connections:
   - Check table shows all connections
   - Verify statuses are "connected"
   - Click "Metrics" to see data

5. Update Prometheus:
   - Edit `prometheus.yml`
   - Change target from `192.168.1.50:8000` to `192.168.1.100:8000`
   - Reload Prometheus config

6. Decommission old server:
   ```bash
   # On old server
   docker compose down
   ```

**Result:** Seamless migration with zero data loss.

---

### Scenario 4: Monitoring Additional Processing Channels

**Context:** You're currently monitoring `A-HD-1` but need to add `A-HD-2`, `A-HD-3`, and `B-HD-1`.

**Workflow:**

1. **Edit Existing Connection:**
   - Click "Edit" on the SNP connection
   - Scroll to "Object ID Subscriptions" section

2. **Add New Channels:**
   
   **For A-HD-2:**
   - Object Type: `procChannelHD`
   - Element IP: `127.0.0.1`
   - Object ID: `A-HD-2`
   - Click "Add Object ID"
   
   **For A-HD-3:**
   - Object Type: `procChannelHD`
   - Element IP: `127.0.0.1`
   - Object ID: `A-HD-3`
   - Click "Add Object ID"
   
   **For B-HD-1:**
   - Object Type: `procChannelHD`
   - Element IP: `127.0.0.1`
   - Object ID: `B-HD-1`
   - Click "Add Object ID"

3. **Verify JSON Preview:**
   ```json
   [
     ...existing objects...,
     {
       "elementIP": "127.0.0.1",
       "objectType": "procChannelHD",
       "objectId": "A-HD-2"
     },
     {
       "elementIP": "127.0.0.1",
       "objectType": "procChannelHD",
       "objectId": "A-HD-3"
     },
     {
       "elementIP": "127.0.0.1",
       "objectType": "procChannelHD",
       "objectId": "B-HD-1"
     }
   ]
   ```

4. **Save and Verify:**
   - Click "Save"
   - Worker restarts automatically
   - Check metrics endpoint:
     ```bash
     curl http://localhost:8000/metrics/ | grep aco_abstatus
     ```
   - Should see metrics for all channels

---

### Scenario 5: Recovering from Accidental Deletion

**Context:** You accidentally deleted a connection and need to restore it.

**Workflow (If you have export backup):**

1. **Locate Export File:**
   - Find most recent export: `snp-connections-2026-02-03.json`

2. **Import File:**
   - Click "Import" button
   - Select export file
   - Confirm import

3. **Verify:**
   - Connection restored with same configuration
   - New database ID assigned
   - Metrics start flowing

**Workflow (If no backup):**

1. **Manually Re-add:**
   - Click "Add Connection"
   - Fill in all fields from memory/documentation
   - Save

2. **Prevention:**
   - Export configuration regularly
   - Store backups off-server
   - Use version control for exports

---

## Appendix

### Example: Minimal Connection

Simplest possible connection for basic system monitoring:

```
Name: Test-SNP
REST API URL: https://192.168.90.23:9089/api/auth
WebSocket URL: wss://192.168.90.23/smm
Username: admin
Password: password
Enabled: ✓

Objects:
  - Object Type: system
    Element IP: 127.0.0.1
```

### Example: Comprehensive Connection

Full monitoring setup with all object types:

```
Name: Production-SNP-Primary
REST API URL: https://192.168.90.23:9089/api/auth
WebSocket URL: wss://192.168.90.23/smm
Username: monitoring
Password: $ecur3P@ss2026
Enabled: ✓

Objects:
  1. Object Type: ptp
     Element IP: 127.0.0.1
  
  2. Object Type: system
     Element IP: 127.0.0.1
  
  3. Object Type: ipVidRx
     Element IP: 127.0.0.1
  
  4. Object Type: procChannelHD
     Element IP: 127.0.0.1
     Object ID: A-HD-1
  
  5. Object Type: procChannelHD
     Element IP: 127.0.0.1
     Object ID: A-HD-2
  
  6. Object Type: procChannelHD
     Element IP: 127.0.0.1
     Object ID: B-HD-1
```

### Example: Export File with Multiple Connections

```json
{
  "version": "1.0",
  "exported_at": "2026-02-03 21:00:00",
  "connections": [
    {
      "name": "Studio-A-Primary",
      "restapi": "https://192.168.90.23:9089/api/auth",
      "websocket": "wss://192.168.90.23/smm",
      "username": "admin",
      "password": "password",
      "objects_ids": [
        {"elementIP": "127.0.0.1", "objectType": "ptp"},
        {"elementIP": "127.0.0.1", "objectType": "system"}
      ],
      "enabled": true
    },
    {
      "name": "Studio-A-Backup",
      "restapi": "https://192.168.90.24:9089/api/auth",
      "websocket": "wss://192.168.90.24/smm",
      "username": "admin",
      "password": "password",
      "objects_ids": [
        {"elementIP": "127.0.0.1", "objectType": "system"}
      ],
      "enabled": false
    },
    {
      "name": "MCR-SNP",
      "restapi": "https://192.168.90.33:9089/api/auth",
      "websocket": "wss://192.168.90.33/smm",
      "username": "monitor",
      "password": "Monitor123",
      "objects_ids": [
        {"elementIP": "127.0.0.1", "objectType": "ptp"},
        {"elementIP": "127.0.0.1", "objectType": "system"},
        {"elementIP": "127.0.0.1", "objectType": "ipVidRx"},
        {"elementIP": "127.0.0.1", "objectType": "procChannelHD", "objectId": "A-HD-1"},
        {"elementIP": "127.0.0.1", "objectType": "procChannelHD", "objectId": "A-HD-5"}
      ],
      "enabled": true
    }
  ]
}
```

---

**Document Version:** 1.0
**Last Updated:** 2026-02-03
**For Application Version:** SNP Exporter v2.0
