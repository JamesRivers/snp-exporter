# SNP Exporter Documentation Index

Welcome to the SNP Exporter documentation. This guide will help you find the information you need.

---

## For Users

### ⚡ Quick Start (Docker Hub)
**File:** `QUICKSTART.md`
- **START HERE** for fastest installation
- 5-minute setup using pre-built image
- Step-by-step with verification
- Common commands for daily use
- Troubleshooting basics

### 🚀 Getting Started
**File:** `README.md`
- Installation options (Docker Hub, Compose, Source)
- Basic overview of features
- Common commands
- Environment variables

### 📘 Operations Guide  
**File:** `OPERATIONS.md` (43 KB)
- **START HERE** for day-to-day usage
- Step-by-step connection management
- Detailed field descriptions with examples
- Export/Import procedures
- Troubleshooting guide
- Workflow examples
- Quick reference tables

**Covers:**
- Adding connections (with example values)
- Editing connections
- Deleting connections
- Export and import procedures
- Monitoring with Prometheus
- Common troubleshooting scenarios
- Best practices

---

## For Developers and Technical Staff

### 🔧 Technical Documentation
**File:** `TECHNICAL.md` (43 KB)
- Complete architecture overview
- Technology stack details
- Code structure and responsibilities
- Technical interconnects
- Data flow diagrams
- Database schema
- API endpoint specifications
- Performance characteristics
- Security considerations
- Development guidelines

**Covers:**
- How the code works
- Async architecture patterns
- WebSocket protocol details
- Prometheus integration
- Database design
- Worker lifecycle
- Task management
- Resource usage

---

## Feature-Specific Documentation

### 📊 Implementation Summary
**File:** `IMPLEMENTATION.md` (6.6 KB)
- Overview of changes from original
- Before/After architecture
- Key features added
- File modifications summary

### 🔄 Reload Feature
**File:** `RELOAD_FEATURE.md` (5.4 KB)
- Reload button implementation
- How reload triggering works
- User feedback mechanisms
- Technical details

### 💾 Export/Import Feature
**File:** `EXPORT_IMPORT_FEATURE.md` (8.9 KB)
- Export functionality details
- Import validation logic
- File format specifications
- Use cases and examples
- Security considerations

### 🖥️ Processor Personality Feature
**File:** `PROCESSOR_PERSONALITY_FEATURE.md` (7.7 KB)
- Processor A/B/C/D monitoring
- REST API integration
- Polling mechanism
- Discovered personality types
- Metrics examples

---

## Quick Links by Task

### I want to...

**Install the application quickly (pre-built image)**
→ QUICKSTART.md

**Install the application (all options)**
→ README.md - Getting Started section

**Add my first SNP connection**
→ OPERATIONS.md - Adding Connections section

**Understand what each field means**
→ OPERATIONS.md - Field descriptions (Step 2)

**Export my configuration**
→ OPERATIONS.md - Export and Import section

**Fix a connection showing "error"**
→ OPERATIONS.md - Troubleshooting section

**Understand how the code works**
→ TECHNICAL.md - Architecture section

**See all available metrics**
→ README.md - Prometheus Metrics section

**Migrate to a new server**
→ OPERATIONS.md - Scenario 3

**Add processor personality monitoring**
→ PROCESSOR_PERSONALITY_FEATURE.md

**Understand the database schema**
→ TECHNICAL.md - Database Schema section

**Configure Prometheus to scrape this exporter**
→ OPERATIONS.md - Monitoring with Prometheus section

**Troubleshoot connection issues**
→ OPERATIONS.md - Troubleshooting section

---

## Documentation Overview

| Document | Size | Audience | Purpose |
|----------|------|----------|---------|
| **QUICKSTART.md** | 10 KB | New Users | 5-minute Docker Hub setup ⭐ |
| **README.md** | 8 KB | All Users | Installation options and overview |
| **OPERATIONS.md** | 44 KB | Operators | Complete user guide ⭐ |
| **TECHNICAL.md** | 43 KB | Developers | Architecture and code details |
| **PROJECT_SUMMARY.md** | 18 KB | Reviewers | Project completion summary |
| **IMPLEMENTATION.md** | 6.6 KB | Reviewers | What was changed |
| **RELOAD_FEATURE.md** | 5.4 KB | Developers | Reload button details |
| **EXPORT_IMPORT_FEATURE.md** | 8.9 KB | Developers | Export/Import details |
| **PROCESSOR_PERSONALITY_FEATURE.md** | 7.7 KB | Developers | Processor monitoring details |

**Total Documentation:** ~150 KB across 10 files

---

## Documentation Standards

### File Naming
- `*.md` - Markdown format
- ALL_CAPS for feature docs
- Title case for guides

### Structure
- Table of contents for long docs
- Headers for navigation
- Code examples with syntax highlighting
- Real-world scenarios and workflows

### Maintenance
- Update when features change
- Keep examples current
- Verify code samples work
- Update version numbers

---

## Getting Help

### Log Analysis
```bash
# View real-time logs
docker logs -f observe-snpexporter

# Search for specific connection
docker logs observe-snpexporter | grep "Studio-A-SNP"

# Find errors
docker logs observe-snpexporter | grep ERROR

# Check last 50 lines
docker logs observe-snpexporter --tail 50
```

### Health Checks
```bash
# Container running?
docker ps | grep observe-snpexporter

# Ports accessible?
curl http://localhost:8080/
curl http://localhost:8000/metrics/

# Database exists?
docker exec observe-snpexporter ls -lh /etc/snp_exporter/connections.db

# API responding?
curl http://localhost:8080/api/connections
```

### Common Commands Reference

```bash
# Start application
docker compose up -d

# Stop application
docker compose down

# View logs
docker logs observe-snpexporter

# Follow logs
docker logs -f observe-snpexporter

# Restart application
docker compose restart

# Rebuild after code changes
docker compose build --no-cache
docker compose up -d

# Access database directly
docker exec -it observe-snpexporter sqlite3 /etc/snp_exporter/connections.db

# Export via CLI
curl http://localhost:8080/api/export > backup.json

# Import via CLI
curl -X POST http://localhost:8080/api/import \
  -H "Content-Type: application/json" \
  -d @backup.json

# Trigger reload
curl http://localhost:8000/-/reload

# Check specific connection
curl http://localhost:8080/api/connections/1 | jq
```

---

## Support

For technical issues, bugs, or feature requests:
1. Check OPERATIONS.md troubleshooting section
2. Review application logs
3. Check TECHNICAL.md for architecture details
4. Contact development team

---

**Last Updated:** 2026-02-03
**Application Version:** 2.0
**Documentation Version:** 1.0
