# SNP Exporter - Quick Start Guide (Docker Hub)

## 5-Minute Quick Start

Get the SNP Exporter running in under 5 minutes using the pre-built Docker image.

---

## Step 1: Pull the Image

```bash
docker pull rivers1980/snp-metrics-exporter:0.1
```

**What this does:** Downloads the pre-built SNP Exporter image (~263 MB).

---

## Step 2: Create Data Directory

```bash
mkdir -p /opt/snp_exporter
```

**What this does:** Creates a directory to persist the SQLite database.

---

## Step 3: Run the Container

```bash
docker run -d \
  --name observe-snpexporter \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 8080:8080 \
  -v /opt/snp_exporter:/etc/snp_exporter \
  -e LOGGING=INFO \
  -e INTERVAL=5 \
  -e POLL_INTERVAL=10 \
  rivers1980/snp-metrics-exporter:0.1
```

**What this does:**
- Creates container named `observe-snpexporter`
- Auto-restarts on failure or server reboot
- Exposes port 8000 (metrics) and 8080 (web UI)
- Mounts `/opt/snp_exporter` for database persistence
- Sets environment variables for logging and intervals

---

## Step 4: Verify It's Running

```bash
docker ps | grep observe-snpexporter
```

**Expected output:**
```
CONTAINER ID   IMAGE                                    STATUS         PORTS
abc123def456   rivers1980/snp-metrics-exporter:0.1      Up 10 seconds  0.0.0.0:8000->8000/tcp, 0.0.0.0:8080->8080/tcp
```

**Check logs:**
```bash
docker logs observe-snpexporter
```

**Expected output:**
```
INFO     Database initialized
INFO     Starting Uvicorn FastAPI metrics server on port 8000
INFO     Starting Uvicorn FastAPI UI server on port 8080
INFO     Starting reloader task
Uvicorn running on http://0.0.0.0:8000
Uvicorn running on http://0.0.0.0:8080
```

---

## Step 5: Access the Web UI

Open your web browser and navigate to:

```
http://{your-server-ip}:8080/
```

**Example:**
- If running on local machine: `http://localhost:8080/`
- If running on server at 192.168.1.100: `http://192.168.1.100:8080/`

You should see the SNP Exporter web interface with:
- "SNP Connections" header
- "Add Connection" button
- Empty connection table (no connections yet)

---

## Step 6: Add Your First SNP Connection

1. **Click the blue "Add Connection" button**

2. **Fill in the form:**
   ```
   Name: Studio-SNP
   REST API URL: https://192.168.90.23:9089/api/auth
   WebSocket URL: wss://192.168.90.23/smm
   Username: admin
   Password: password
   Enabled: ✓ (checked)
   ```

3. **Add object subscriptions:**
   - Object Type: `system`
   - Element IP: `127.0.0.1`
   - Click "Add Object ID"

4. **Click "Save"**

5. **Wait 10 seconds and verify:**
   - Connection appears in table
   - Status shows 🟢 Connected
   - Last Update timestamp is recent

---

## Step 7: View Metrics

Click the cyan "Metrics" button on your connection row.

A new tab opens showing Prometheus metrics:
```
ic_snp_api_status{target="Studio-SNP"} 1.0
ic_snp_mainboard_temperature{target="Studio-SNP"} 49.0
ic_snp_processor_personality_info{personality="Multiviewer",processor="processorA",target="Studio-SNP"} 1.0
...
```

---

## 🎉 You're Done!

Your SNP Exporter is now:
- ✅ Running in Docker
- ✅ Connected to your SNP device
- ✅ Collecting metrics
- ✅ Exposing data for Prometheus

---

## Common Commands

### Daily Operations

```bash
# View logs
docker logs -f observe-snpexporter

# Check status
docker ps | grep observe-snpexporter

# Restart container
docker restart observe-snpexporter

# Stop container
docker stop observe-snpexporter

# Start container
docker start observe-snpexporter
```

### Maintenance

```bash
# Export configuration backup
curl http://localhost:8080/api/export > backup-$(date +%Y%m%d).json

# Update to latest version
docker stop observe-snpexporter
docker rm observe-snpexporter
docker pull rivers1980/snp-metrics-exporter:0.1
docker run -d \
  --name observe-snpexporter \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 8080:8080 \
  -v /opt/snp_exporter:/etc/snp_exporter \
  -e LOGGING=INFO \
  rivers1980/snp-metrics-exporter:0.1

# View database contents
docker exec observe-snpexporter sqlite3 /etc/snp_exporter/connections.db "SELECT id, name, enabled FROM snp_connections;"

# Remove everything (including database)
docker stop observe-snpexporter
docker rm observe-snpexporter
rm -rf /opt/snp_exporter
```

---

## Using Docker Compose (Alternative)

If you prefer Docker Compose management:

1. **Create docker-compose.yml:**
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
       volumes:
         - ./data:/etc/snp_exporter/
   ```

2. **Common commands:**
   ```bash
   # Start
   docker compose up -d
   
   # Stop
   docker compose down
   
   # View logs
   docker compose logs -f
   
   # Restart
   docker compose restart
   
   # Update image
   docker compose pull
   docker compose up -d
   ```

---

## Next Steps

Now that your exporter is running:

1. **Add more connections** - Monitor all your SNP devices
2. **Export configuration** - Create a backup
3. **Configure Prometheus** - Add exporter to scrape config
4. **Create dashboards** - Build Grafana visualizations
5. **Set up alerts** - Configure alerting rules

For detailed instructions, see:
- **OPERATIONS.md** - Complete user guide
- **TECHNICAL.md** - Architecture details
- **README.md** - Feature overview

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs observe-snpexporter

# Common issues:
# - Port already in use: Change -p 8000:8001 or stop conflicting service
# - Permission denied: Use sudo or add user to docker group
# - Image not found: Verify image name is correct
```

### Can't access web UI

```bash
# Verify container is running
docker ps | grep observe-snpexporter

# Check ports
sudo netstat -tlnp | grep 8080

# Try localhost
curl http://localhost:8080/

# Check firewall
sudo ufw status
```

### Connection shows "error"

- Verify SNP device IP is correct
- Test SNP web login manually
- Check username/password
- Verify network connectivity: `ping 192.168.90.23`

---

## Need Help?

- **User Guide:** OPERATIONS.md
- **Technical Details:** TECHNICAL.md
- **All Documentation:** DOCUMENTATION_INDEX.md

---

**Docker Hub:** `rivers1980/snp-metrics-exporter:0.1`
**Web UI:** http://localhost:8080/
**Metrics:** http://localhost:8000/metrics/
