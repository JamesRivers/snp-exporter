# Console Metrics Feature Implementation

**Feature**: Add Console-Level Metrics to SNP Exporter  
**Date**: 2026-02-04  
**Status**: In Development  

---

## Overview

This document tracks the implementation of console-level metrics collection for the SNP Exporter. These metrics provide system-level information that is not available through the WebSocket status feed and requires dedicated REST API polling.

---

## Objectives

Add support for the following metrics:

1. **System Uptime** - Time since last system boot
2. **Power On Time** - Cumulative time system has been powered on
3. **Control Link Bonding** - Network bonding configuration status

---

## API Endpoints

### 1. Console Status API

**Endpoint**: `GET /api/console/status`  
**API Reference**: #45 in SNP_RESTful_API.pdf  
**Authentication**: Required (JWT Bearer token)  
**Works On**: Self-hosted SNP only  

**Purpose**: Retrieve system status including uptime and power on time

**Request Example**:
```bash
curl -k -X GET \
  -H "Authorization: Bearer {token}" \
  https://{SNP-IP}:9089/api/console/status
```

**Response Structure**: (To be documented after testing)

```json
{
  "uptime": "...",
  "powerOnTime": "...",
  ...
}
```

### 2. System Configuration API

**Endpoint**: `GET /api/elements/{ip}/config/system`  
**API Reference**: #17 in SNP_RESTful_API.pdf  
**Authentication**: Required (JWT Bearer token)  

**Purpose**: Retrieve system configuration including control link bonding mode

**Request Example**:
```bash
curl -k -X GET \
  -H "Authorization: Bearer {token}" \
  https://{SNP-IP}:9089/api/elements/127.0.0.1/config/system
```

**Response Structure**:
```json
{
  "type": "system",
  "object_ID": "system",
  "config": "{\"System_Control\":{\"Net_Mode\":\"dual\"},...}"
}
```

**Net_Mode Values** (Expected from API docs):
- `"dual"` - Dual Addresses (not bonded)
- `"bondedActiveBackup"` - Bonded Active/Backup
- `"bondedLACP"` - Bonded LACP

**Actual Net_Mode Values** (Discovered from testing):
- `"Dual Addresses"` - Dual network interfaces (not bonded)
- `"Bonded Active/Backup"` - Bonded Active/Backup (assumed)
- `"Bonded LACP"` - Bonded LACP (assumed)

---

## API Testing Results

### Test Environment
- **SNP Device IP**: 192.168.90.33
- **Firmware Version**: 3.1.0.62
- **Firmware Date**: 2025-04-23
- **Serial Number**: 2117480213
- **Test Date**: 2026-02-04

### Console Status API Test ✅

**Command**:
```bash
TOKEN=$(curl -k -s -X POST -H "Content-Type:application/json" \
  -d '{"username":"admin","password":"password"}' \
  https://192.168.90.33:9089/api/auth)

curl -k -s -X GET -H "Authorization:$TOKEN" \
  https://192.168.90.33:9089/api/console/status
```

**Response** (Abbreviated - Key Fields):
```json
{
    "operation": "",
    "data": {
        "upTime": "up 2 weeks, 1 hour, 25 minutes",
        "pwrOnTime": "14 days 01 hours 26 minutes 09 sec",
        "netMode": "dual",
        "logLevel": "6",
        "remoteLogger": "0.0.0.0:0",
        "serialNum": "2117480213",
        "firmwareVer": "3.1.0.62",
        "firmwareDate": "2025-04-23 22:50:05",
        "mainBoardRevision": "1",
        "chassisType": "SNP Chassis",
        "ioBoardRevision": "1",
        "interfaces": [
            {
                "id": "ctrl1",
                "ip": "192.168.90.33",
                "mask": "255.255.255.0",
                "gateway": "192.168.90.2",
                "mac": "00:90:f9:34:6C:AD",
                "dhcp": false
            },
            {
                "id": "ctrl2",
                "ip": "10.0.14.21",
                "mask": "255.255.248.0",
                "gateway": "10.0.14.254",
                "mac": "00:90:f9:34:6C:AE",
                "dhcp": false
            }
        ]
    }
}
```

**Findings**:
- ✅ API endpoint works perfectly
- ✅ Returns comprehensive console status data
- ✅ **upTime** field format: `"up X weeks, X hours, X minutes"` (string format)
- ✅ **pwrOnTime** field format: `"X days X hours X minutes X sec"` (string format)
- ✅ **netMode** field: `"dual"` (matches expected values)
- ⚠️ **Note**: Both time fields are human-readable strings, NOT seconds
- ⚠️ **Parsing Required**: Need to convert strings to seconds for Prometheus metrics
- ✅ Additional useful data: serialNum, firmwareVer, interfaces

### System Config API Test ✅

**Command**:
```bash
TOKEN=$(curl -k -s -X POST -H "Content-Type:application/json" \
  -d '{"username":"admin","password":"password"}' \
  https://192.168.90.33:9089/api/auth)

curl -k -s -X GET -H "Authorization:$TOKEN" \
  https://192.168.90.33:9089/api/elements/127.0.0.1/config/system
```

**Response** (System_Control section):
```json
{
  "System_Control": {
    "Eth0_ipAddr": "192.168.90.33",
    "Eth0_netmask": "255.255.255.0",
    "Eth0_gateway": "192.168.90.2",
    "Eth1_ipAddr": "10.0.14.21",
    "Eth1_netmask": "255.255.248.0",
    "Eth1_gateway": "10.0.14.254",
    "Net_Mode": "Dual Addresses",
    "Eth0_dhcp": false,
    "Eth1_dhcp": false
  }
}
```

**Findings**:
- ✅ API endpoint works perfectly
- ✅ **Net_Mode** field found in System_Control
- ⚠️ **Actual value**: `"Dual Addresses"` (with space and title case)
- ⚠️ **Documentation mismatch**: API docs say `"dual"`, actual value is `"Dual Addresses"`
- ⚠️ **Parsing Required**: Need to normalize/map Net_Mode values
- ✅ Additional data: Network interface configurations available

### Critical Implementation Notes

#### Time String Parsing

**upTime format**: `"up 2 weeks, 1 hour, 25 minutes"`  
**pwrOnTime format**: `"14 days 01 hours 26 minutes 09 sec"`

**Parsing Strategy**:
1. Extract numeric values using regex
2. Convert to total seconds:
   - weeks → × 604800 seconds
   - days → × 86400 seconds  
   - hours → × 3600 seconds
   - minutes → × 60 seconds
   - seconds → × 1 second

**Example Implementation**:
```python
def parse_uptime(uptime_str):
    """Parse 'up 2 weeks, 1 hour, 25 minutes' to seconds"""
    import re
    seconds = 0
    weeks = re.search(r'(\d+)\s*week', uptime_str)
    days = re.search(r'(\d+)\s*day', uptime_str)
    hours = re.search(r'(\d+)\s*hour', uptime_str)
    minutes = re.search(r'(\d+)\s*minute', uptime_str)
    
    if weeks: seconds += int(weeks.group(1)) * 604800
    if days: seconds += int(days.group(1)) * 86400
    if hours: seconds += int(hours.group(1)) * 3600
    if minutes: seconds += int(minutes.group(1)) * 60
    
    return seconds

def parse_power_on_time(time_str):
    """Parse '14 days 01 hours 26 minutes 09 sec' to seconds"""
    import re
    seconds = 0
    days = re.search(r'(\d+)\s*day', time_str)
    hours = re.search(r'(\d+)\s*hour', time_str)
    minutes = re.search(r'(\d+)\s*minute', time_str)
    secs = re.search(r'(\d+)\s*sec', time_str)
    
    if days: seconds += int(days.group(1)) * 86400
    if hours: seconds += int(hours.group(1)) * 3600
    if minutes: seconds += int(minutes.group(1)) * 60
    if secs: seconds += int(secs.group(1))
    
    return seconds
```

#### Net_Mode Value Mapping

**Observed Values** → **Normalized Values** → **Metric Value**:
- `"Dual Addresses"` → `dual` → 0
- `"Bonded Active/Backup"` → `bonded_active_backup` → 1
- `"Bonded LACP"` → `bonded_lacp` → 2

**Implementation**:
```python
def normalize_net_mode(net_mode_str):
    """Normalize Net_Mode string to standard format"""
    mode_map = {
        "dual addresses": "dual",
        "bonded active/backup": "bonded_active_backup",
        "bonded lacp": "bonded_lacp"
    }
    return mode_map.get(net_mode_str.lower(), "unknown")
```

---

## Prometheus Metrics Design

### Metric Definitions

#### 1. ic_snp_console_uptime_seconds
**Type**: Gauge  
**Labels**: target  
**Description**: System uptime since last boot (seconds)  
**Unit**: Seconds  

**Example**:
```prometheus
ic_snp_console_uptime_seconds{target="SNP-192.168.90.33"} 3456789.0
```

#### 2. ic_snp_console_power_on_time_seconds
**Type**: Gauge  
**Labels**: target  
**Description**: Cumulative power-on time (seconds)  
**Unit**: Seconds  

**Example**:
```prometheus
ic_snp_console_power_on_time_seconds{target="SNP-192.168.90.33"} 12345678.0
```

#### 3. ic_snp_console_info
**Type**: Info  
**Labels**: target, uptime_formatted, power_on_formatted  
**Description**: Console information with human-readable time formats  

**Example**:
```prometheus
ic_snp_console_info{target="SNP-192.168.90.33",uptime_formatted="40d 01h 59m",power_on_formatted="142d 21h 21m"} 1.0
```

#### 4. ic_snp_control_link_bonding_status
**Type**: Gauge  
**Labels**: target  
**Description**: Control link bonding status (0=dual, 1=bonded_active_backup, 2=bonded_lacp)  
**Values**: 0, 1, or 2  

**Example**:
```prometheus
ic_snp_control_link_bonding_status{target="SNP-192.168.90.33"} 0.0
```

#### 5. ic_snp_control_link_bonding_info
**Type**: Info  
**Labels**: target, mode  
**Description**: Control link bonding mode information  

**Example**:
```prometheus
ic_snp_control_link_bonding_info{target="SNP-192.168.90.33",mode="dual"} 1.0
```

---

## Implementation Architecture

### Background Polling Task

**Function**: `poll_console_metrics()`  
**Polling Interval**: 60 seconds  
**Concurrent with**: WebSocket listener, processor personality poller  

**Flow**:
```
1. Sleep 60 seconds
2. Get JWT authentication token
3. Fetch console status (GET /api/console/status)
4. Parse uptime and power_on_time
5. Update Prometheus metrics
6. Fetch system config (GET /api/elements/{ip}/config/system)
7. Parse Net_Mode
8. Update bonding metrics
9. Loop back to step 1
```

**Error Handling**:
- Token retrieval failure: Log warning, retry next cycle
- API endpoint unavailable: Log error, continue (graceful degradation)
- Parse errors: Log error, skip metric update for this cycle

### Task Lifecycle

Each worker spawns **3 concurrent async tasks**:
1. **WebSocket Listener** - Real-time status updates
2. **Processor Personality Poller** - Poll every 60s
3. **Console Metrics Poller** - Poll every 60s (NEW)

**Cleanup on Worker Stop**:
- All 3 tasks cancelled
- Metrics removed from Prometheus registry
- Resources cleaned up

---

## Code Structure

### New Functions

1. **`get_console_status(name, base_url, token)`**
   - Async function to fetch console status
   - Returns dict with uptime and power_on_time
   - Handles errors gracefully

2. **`get_system_config(name, base_url, token, element_ip)`**
   - Async function to fetch system configuration
   - Extracts Net_Mode from System_Control
   - Returns string: "dual", "bondedActiveBackup", or "bondedLACP"

3. **`poll_console_metrics(name, rest_url, ws_url, username, password)`**
   - Background async task
   - Polls both console status and system config
   - Updates all 5 Prometheus metrics
   - Runs indefinitely until cancelled

4. **`format_uptime(seconds)`**
   - Helper function to format seconds as "XdXhXm"
   - Returns human-readable string

5. **`extract_element_ip(ws_url)`**
   - Helper to extract element IP from WebSocket URL
   - Used for system config API calls

### Modified Functions

1. **`worker()`**
   - Add console polling task to background tasks
   - Ensure proper cancellation on shutdown

2. **`remove_metrics(target)`**
   - Add new console metrics to cleanup

---

## Performance Impact

### Resource Usage

**Per Connection**:
- +1 background async task
- +2 REST API calls per minute (console status + system config)
- +~100 bytes memory for metric storage

**For 10 Connections**:
- +10 async tasks (total: 30 tasks)
- +20 API calls/minute (very light load)
- Negligible CPU/memory impact

### API Rate Limiting

**Total API Calls per Connection per Minute**:
- Authentication: ~2-3 calls/min (tokens for each polling task)
- Processor personality: 1 call/min
- Console status: 1 call/min
- System config: 1 call/min
- **Total**: ~5-6 calls/min per connection

**Assessment**: Very light API load, no rate limiting concerns

---

## Testing Plan

### Phase 1: API Discovery ✅
- [x] Read API documentation
- [ ] Test console status endpoint with live device
- [ ] Test system config endpoint with live device
- [ ] Document exact response structures
- [ ] Identify field names and data types

### Phase 2: Implementation
- [ ] Add metric definitions to main.py
- [ ] Implement helper functions
- [ ] Implement API fetch functions
- [ ] Implement polling task
- [ ] Update worker lifecycle
- [ ] Update cleanup function

### Phase 3: Unit Testing
- [ ] Test with single connection
- [ ] Verify metrics exposed in /metrics endpoint
- [ ] Check metric values are correct
- [ ] Verify polling happens every 60 seconds
- [ ] Test error handling (invalid credentials, API timeout)

### Phase 4: Integration Testing
- [ ] Test with multiple connections (2-3 devices)
- [ ] Test worker restart/reload
- [ ] Test connection add/delete
- [ ] Monitor logs for errors
- [ ] Check for memory leaks or task accumulation

### Phase 5: Documentation
- [ ] Update README.md
- [ ] Update COMPREHENSIVE_METRICS.md
- [ ] Update TECHNICAL.md
- [ ] Create Grafana dashboard examples

---

## Grafana Dashboard Examples

### Panel: System Uptime

**Type**: Stat  
**Query**:
```promql
ic_snp_console_uptime_seconds{target="$target"} / 86400
```
**Unit**: Days  
**Decimals**: 1  

### Panel: Power On Time

**Type**: Stat  
**Query**:
```promql
ic_snp_console_power_on_time_seconds{target="$target"} / 3600
```
**Unit**: Hours  
**Decimals**: 0  

### Panel: Uptime Graph

**Type**: Time Series  
**Query**:
```promql
ic_snp_console_uptime_seconds{target=~"$target"} / 86400
```
**Legend**: {{ target }}  
**Y-Axis**: Days  

### Panel: Control Link Bonding

**Type**: Stat  
**Query**:
```promql
ic_snp_control_link_bonding_info{target="$target"}
```
**Value Mappings**:
- dual → "Dual Addresses"
- bondedActiveBackup → "Active/Backup"
- bondedLACP → "LACP"

---

## Alert Examples

### System Reboot Detection

```yaml
- alert: SNPSystemRebooted
  expr: ic_snp_console_uptime_seconds < 300
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "SNP {{ $labels.target }} recently rebooted (uptime < 5 minutes)"
```

### Bonding Configuration Change

```yaml
- alert: SNPBondingModeChanged
  expr: changes(ic_snp_control_link_bonding_status[5m]) > 0
  labels:
    severity: info
  annotations:
    summary: "SNP {{ $labels.target }} bonding mode changed"
```

---

## Known Limitations

### 1. Self-Hosted SNP Only
**Issue**: Console status API documented as "works for self-host only"  
**Impact**: May not work with remote SNP Manager deployments  
**Mitigation**: Graceful error handling, log warnings if unavailable  
**Status**: To be verified during testing  

### 2. Firmware Version Compatibility
**Issue**: API availability may depend on firmware version  
**Impact**: Older firmware may not have console status endpoint  
**Mitigation**: Check response codes, don't crash worker if unavailable  
**Status**: Unknown, needs testing with multiple firmware versions  

### 3. Element IP Extraction
**Issue**: Need to extract element IP from WebSocket URL or connection config  
**Impact**: Required for system config API calls  
**Solution**: Parse from ws_url or use 127.0.0.1 as default  
**Status**: To be implemented  

---

## Implementation Checklist

### Code Changes
- [ ] Add 5 metric definitions (lines ~90-110)
- [ ] Add `format_uptime()` helper function
- [ ] Add `extract_element_ip()` helper function
- [ ] Add `get_console_status()` function
- [ ] Add `get_system_config()` function
- [ ] Add `poll_console_metrics()` function
- [ ] Update `worker()` function to spawn console task
- [ ] Update `remove_metrics()` function

### Documentation Changes
- [ ] Update README.md - Prometheus Metrics section
- [ ] Update COMPREHENSIVE_METRICS.md - Add console metrics section
- [ ] Update TECHNICAL.md - Document console API endpoints
- [ ] Create alert examples
- [ ] Create Grafana dashboard examples

### Testing
- [ ] Test API endpoints manually with curl
- [ ] Test with single SNP connection
- [ ] Test with multiple SNP connections
- [ ] Test error scenarios
- [ ] Verify metrics accuracy

---

## Success Criteria

Implementation complete when:
- ✅ All 5 console metrics exposed in /metrics endpoint
- ✅ Metrics update every 60 seconds
- ✅ No errors during normal operation
- ✅ Graceful handling when APIs unavailable
- ✅ Documentation updated
- ✅ Tested with live SNP devices

---

## Rollback Plan

If issues arise:
1. Comment out console polling task spawn in worker()
2. Comment out metric definitions
3. Restart application
4. All other functionality remains intact (backward compatible)

---

## Future Enhancements

### Optimization: Token Caching
**Current**: Get fresh token for each API call  
**Proposed**: Cache token, reuse across polling tasks  
**Benefit**: Reduce API calls by ~50%  
**Priority**: Low (current approach works fine)  

### Enhancement: Additional Console Metrics
**Possible additions from console status API**:
- System time
- System date
- Timezone
- Network interface statistics

**Priority**: Medium (after initial implementation proven)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-04 | Initial documentation created | OpenCode |
| 2026-02-04 | API testing in progress | OpenCode |

---

## References

- SNP_RESTful_API.pdf - Official API documentation
- SNP_REST_API_examples_using_cURL.pdf - cURL examples
- TECHNICAL.md - Existing technical documentation
- COMPREHENSIVE_METRICS.md - Existing metrics documentation

---

**Status**: 🔄 API Testing Phase  
**Next Step**: Test console status endpoint with live SNP device
