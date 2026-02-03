# PTP Metrics - Comprehensive Documentation

## Overview

The SNP Exporter now exposes comprehensive PTP (Precision Time Protocol) metrics including timing status, master information, clock identity, and synchronization statistics.

## Metrics Exposed

### 1. ic_snp_ptp_status
**Type:** Gauge
**Description:** PTP controller lock status
**Values:**
- `1.0` = Locked (synchronized with master)
- `0.0` = Unlocked/Free Run (not synchronized)

**Example:**
```prometheus
ic_snp_ptp_status{target="SNP-192.168.90.33"} 1.0
```

**Use Case:** Primary alert metric for PTP synchronization health

---

### 2. ic_snp_ptp_master_offset
**Type:** Gauge
**Unit:** Microseconds (μs)
**Description:** Offset from PTP master clock

**Example:**
```prometheus
ic_snp_ptp_master_offset{target="SNP-192.168.90.33"} 0.642
```

**Interpretation:**
- Close to 0: Good synchronization
- Large values: Potential timing issues
- Rapidly changing: Network jitter

**Alert Threshold:** > 1.0 μs may indicate issues

---

### 3. ic_snp_ptp_master_delay
**Type:** Gauge
**Unit:** Microseconds (μs)
**Description:** Network delay to PTP master

**Example:**
```prometheus
ic_snp_ptp_master_delay{target="SNP-192.168.90.33"} 0.169
```

**Interpretation:**
- Low values: Good network path
- High values: Network congestion or long path
- Sudden increases: Network issues

**Typical Values:** 0.1 - 1.0 μs on local network

---

### 4. ic_snp_ptp_is_master
**Type:** Gauge
**Description:** PTP role indicator
**Values:**
- `1.0` = Master (this device is PTP master)
- `0.0` = Slave (synchronized to external master)

**Example:**
```prometheus
ic_snp_ptp_is_master{target="SNP-192.168.90.33"} 0.0
```

**Use Case:** Identify which SNP devices are masters vs slaves in your network

---

### 5. ic_snp_ptp_biggest_sys_time_update_ms
**Type:** Gauge
**Unit:** Milliseconds (ms)
**Description:** Largest system time correction since last reset

**Example:**
```prometheus
ic_snp_ptp_biggest_sys_time_update_ms{target="SNP-192.168.90.33"} 1004.0
```

**Interpretation:**
- Small values (<10 ms): Normal operation
- Large values (>100 ms): Significant time jump occurred
- Very large (>1000 ms): System clock was way off

**Alert Threshold:** > 500 ms indicates significant time adjustment

---

### 6. ic_snp_ptp_num_sys_time_updates
**Type:** Gauge
**Description:** Count of system time updates performed

**Example:**
```prometheus
ic_snp_ptp_num_sys_time_updates{target="SNP-192.168.90.33"} 23.0
```

**Interpretation:**
- Incrementing: System clock being adjusted
- Static: Stable synchronization
- Rapidly increasing: Frequent adjustments (possible issue)

---

### 7. ic_snp_ptp_info
**Type:** Info
**Description:** Comprehensive PTP information as labels

**Labels:**
- `clock_identity` - Unique PTP clock identifier (MAC-based)
- `controller_state` - Detailed state (e.g., "Locked", "Unlocked-Free Run")
- `master_ip` - IP address of PTP master
- `master_interface_ip` - Interface IP of PTP master
- `master_uuid` - UUID of PTP master clock
- `master_present` - Master redundancy status
- `utc_time` - Current UTC time from PTP
- `rtc_time` - RTC time (usually "N/A")

**Example:**
```prometheus
ic_snp_ptp_info{
  target="SNP-192.168.90.33",
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

**Use Cases:**
- Identify PTP master in Grafana
- Track master failovers
- Verify clock identity
- Display UTC time in dashboards

---

## PTP Controller States

The `controller_state` label in `ic_snp_ptp_info` can have various values:

| State | Meaning |
|-------|---------|
| `Locked` | Synchronized and stable |
| `Unlocked-Free Run` | Not synchronized, using internal clock |
| `Acquiring` | Attempting to sync with master |
| `Holdover` | Lost master, maintaining last known time |

---

## Example Queries

### PromQL Examples

**Check which SNPs are PTP locked:**
```promql
ic_snp_ptp_status == 1
```

**Find SNPs with PTP issues:**
```promql
ic_snp_ptp_status == 0
```

**Show PTP master IP for all SNPs:**
```promql
ic_snp_ptp_info
```

**Calculate PTP offset average over 5 minutes:**
```promql
avg_over_time(ic_snp_ptp_master_offset[5m])
```

**SNPs that had large time corrections:**
```promql
ic_snp_ptp_biggest_sys_time_update_ms > 100
```

**Count SNPs acting as PTP masters:**
```promql
sum(ic_snp_ptp_is_master)
```

---

## Grafana Dashboard Panels

### Panel 1: PTP Lock Status
**Type:** Stat
**Query:**
```promql
ic_snp_ptp_status{target="$target"}
```
**Thresholds:**
- Red: < 1 (Unlocked)
- Green: = 1 (Locked)

### Panel 2: PTP Offset Graph
**Type:** Time Series
**Query:**
```promql
ic_snp_ptp_master_offset{target="$target"}
```
**Y-Axis:** Microseconds
**Alert Line:** ±1.0 μs

### Panel 3: PTP Master Information
**Type:** Table
**Query:**
```promql
ic_snp_ptp_info
```
**Columns:**
- Target
- Master IP
- Controller State
- UTC Time

### Panel 4: Time Update History
**Type:** Stat
**Queries:**
```promql
ic_snp_ptp_biggest_sys_time_update_ms{target="$target"}
ic_snp_ptp_num_sys_time_updates{target="$target"}
```

---

## Alert Rules

### Critical Alerts

**PTP Unlock:**
```yaml
- alert: PTPUnlocked
  expr: ic_snp_ptp_status == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "SNP {{ $labels.target }} PTP unlocked"
    description: "PTP controller is not locked. Timing may be unstable."
```

**Large Time Adjustment:**
```yaml
- alert: PTPLargeTimeUpdate
  expr: ic_snp_ptp_biggest_sys_time_update_ms > 500
  labels:
    severity: warning
  annotations:
    summary: "SNP {{ $labels.target }} large time update: {{ $value }}ms"
    description: "Significant system time correction occurred."
```

### Warning Alerts

**High Offset:**
```yaml
- alert: PTPHighOffset
  expr: abs(ic_snp_ptp_master_offset) > 1.0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "SNP {{ $labels.target }} high PTP offset: {{ $value }}μs"
```

**Frequent Time Updates:**
```yaml
- alert: PTPFrequentUpdates
  expr: rate(ic_snp_ptp_num_sys_time_updates[5m]) > 0.1
  labels:
    severity: warning
  annotations:
    summary: "SNP {{ $labels.target }} frequent time updates"
```

---

## PTP Data Source

**Protocol:** WebSocket (WSS)
**Message Type:** `statusState` / `allStatuses`
**Object Type:** `ptp`
**Update Frequency:** ~1 second (1000ms)

**Subscription:**
```json
{
  "msgType": "statusListSubscribe",
  "frequency": 1000,
  "objectIds": [
    {
      "elementIP": "127.0.0.1",
      "objectType": "ptp"
    }
  ]
}
```

**Response Format:**
```json
{
  "msgType": "statusState",
  "statuses": [
    "{\"name\":\"ptpStatus\",\"object_ID\":\"ptp\",\"ptpStatus\":{...}}"
  ]
}
```

---

## Field Mappings

| SNP Field | Metric Name | Type | Unit |
|-----------|-------------|------|------|
| `ptpCtlrState` | `ic_snp_ptp_status` | Gauge | Boolean (1/0) |
| `ptpMasterOffset` | `ic_snp_ptp_master_offset` | Gauge | Microseconds |
| `ptpMasterDelay` | `ic_snp_ptp_master_delay` | Gauge | Microseconds |
| `ptpUcipIsMaster` | `ic_snp_ptp_is_master` | Gauge | Boolean (1/0) |
| `biggestSysTimeUpdate` | `ic_snp_ptp_biggest_sys_time_update_ms` | Gauge | Milliseconds |
| `numSysTimeUpdates` | `ic_snp_ptp_num_sys_time_updates` | Gauge | Count |
| `clockIdentity` | `ic_snp_ptp_info{clock_identity}` | Info | Label |
| `ptpMasterIP` | `ic_snp_ptp_info{master_ip}` | Info | Label |
| `ptpMasterInterfaceIP` | `ic_snp_ptp_info{master_interface_ip}` | Info | Label |
| `ptpMasterUUID` | `ic_snp_ptp_info{master_uuid}` | Info | Label |
| `ptpMasterPresent` | `ic_snp_ptp_info{master_present}` | Info | Label |
| `ptpUTC` | `ic_snp_ptp_info{utc_time}` | Info | Label |
| `rtcTime` | `ic_snp_ptp_info{rtc_time}` | Info | Label |

---

## Implementation Details

### Code Location
**File:** `src/main.py`
**Function:** `parse_statuses()` (line ~396-422)

### Parsing Logic
```python
elif status_type == "ptp":
    ptp_data = status["ptpStatus"]
    
    # Status metrics
    ptp_status.labels(target=name).set(
        1 if ptp_data["ptpCtlrState"] == "Locked" else 0
    )
    ptp_master_offset.labels(target=name).set(
        safe_float(ptp_data["ptpMasterOffset"].split(" ")[0])
    )
    ptp_master_delay.labels(target=name).set(
        safe_float(ptp_data["ptpMasterDelay"].split(" ")[0])
    )
    
    # Info metric with all details
    ptp_info.labels(target=name).info({
        "clock_identity": ptp_data.get("clockIdentity", "N/A"),
        "controller_state": ptp_data.get("ptpCtlrState", "N/A"),
        "master_ip": ptp_data.get("ptpMasterIP", "N/A"),
        "master_interface_ip": ptp_data.get("ptpMasterInterfaceIP", "N/A"),
        "master_uuid": ptp_data.get("ptpMasterUUID", "N/A"),
        "master_present": ptp_data.get("ptpMasterPresent", "N/A"),
        "utc_time": ptp_data.get("ptpUTC", "N/A"),
        "rtc_time": ptp_data.get("rtcTime", "N/A")
    })
    
    # Numeric statistics
    ptp_biggest_sys_time_update.labels(target=name).set(
        safe_float(ptp_data.get("biggestSysTimeUpdate", "0 ms").split(" ")[0])
    )
    ptp_num_sys_time_updates.labels(target=name).set(
        safe_float(ptp_data.get("numSysTimeUpdates", "0"))
    )
    ptp_is_master.labels(target=name).set(
        1 if ptp_data.get("ptpUcipIsMaster", "Slave") == "Master" else 0
    )
```

---

## Testing

### Verify Metrics

**Check all PTP metrics for a device:**
```bash
curl -s http://localhost:8000/metrics/ | grep "ic_snp_ptp" | grep "SNP-192.168.90.33"
```

**Expected Output:**
```
ic_snp_ptp_status{target="SNP-192.168.90.33"} 1.0
ic_snp_ptp_master_offset{target="SNP-192.168.90.33"} 0.642
ic_snp_ptp_master_delay{target="SNP-192.168.90.33"} 0.169
ic_snp_ptp_info{...} 1.0
ic_snp_ptp_biggest_sys_time_update_ms{target="SNP-192.168.90.33"} 1004.0
ic_snp_ptp_num_sys_time_updates{target="SNP-192.168.90.33"} 23.0
ic_snp_ptp_is_master{target="SNP-192.168.90.33"} 0.0
```

---

## Comparison: Before vs After

### Before (3 metrics)
```prometheus
ic_snp_ptp_status{target="SNP"} 1.0
ic_snp_ptp_master_offset{target="SNP"} 45.0
ic_snp_ptp_master_delay{target="SNP"} 120.0
```

### After (7 metrics)
```prometheus
ic_snp_ptp_status{target="SNP"} 1.0
ic_snp_ptp_master_offset{target="SNP"} 0.642
ic_snp_ptp_master_delay{target="SNP"} 0.169
ic_snp_ptp_is_master{target="SNP"} 0.0
ic_snp_ptp_biggest_sys_time_update_ms{target="SNP"} 1004.0
ic_snp_ptp_num_sys_time_updates{target="SNP"} 23.0
ic_snp_ptp_info{clock_identity="...",master_ip="2.2.2.2",...} 1.0
```

**Added:**
- Master/Slave indicator
- Time update statistics
- Comprehensive info metric with 8 labels
- Better descriptions

---

## Troubleshooting with PTP Metrics

### Issue: PTP shows as unlocked

**Check:**
1. `ic_snp_ptp_status` = 0
2. `ic_snp_ptp_info{controller_state}` = "Unlocked-Free Run"
3. `ic_snp_ptp_info{master_ip}` = "0.0.0.0" (no master)

**Resolution:**
- Verify PTP master is online
- Check network connectivity to master
- Review PTP configuration on SNP device

### Issue: Large timing offsets

**Check:**
1. `ic_snp_ptp_master_offset` > 1.0
2. `ic_snp_ptp_master_delay` increasing
3. `ic_snp_ptp_biggest_sys_time_update_ms` very large

**Resolution:**
- Check network jitter
- Verify PTP master stability
- Review network switches for PTP support

### Issue: Frequent master changes

**Check:**
1. `ic_snp_ptp_info{master_ip}` changing frequently
2. `ic_snp_ptp_info{master_uuid}` changing

**Resolution:**
- Check PTP master redundancy configuration
- Verify network stability
- Review master priority settings

---

## Real-World Examples

### Example 1: Locked SNP Device
```prometheus
ic_snp_ptp_status{target="SNP-192.168.90.33"} 1.0
ic_snp_ptp_master_offset{target="SNP-192.168.90.33"} 0.642
ic_snp_ptp_master_delay{target="SNP-192.168.90.33"} 0.169
ic_snp_ptp_is_master{target="SNP-192.168.90.33"} 0.0
ic_snp_ptp_biggest_sys_time_update_ms{target="SNP-192.168.90.33"} 1004.0
ic_snp_ptp_num_sys_time_updates{target="SNP-192.168.90.33"} 2.0
ic_snp_ptp_info{
  clock_identity="00 90 F9 FF FE 34 6C AF",
  controller_state="Locked",
  master_ip="2.2.2.2",
  master_interface_ip="192.168.61.33",
  master_uuid="00-04-B3-FF-FE-F0-14-7D",
  master_present="Primary/Secondary",
  utc_time="Tue Feb 3 22:04:15 2026",
  rtc_time="N/A",
  target="SNP-192.168.90.33"
} 1.0
```

**Interpretation:**
- ✅ Status: Locked (working)
- ✅ Offset: 0.642 μs (excellent)
- ✅ Delay: 0.169 μs (low latency)
- ✅ Role: Slave (as expected)
- ⚠️ Largest update: 1004 ms (was off by 1 second at some point)
- ✅ Updates: 2 (minimal corrections needed)
- ✅ Master: 2.2.2.2 (known master)
- ✅ Redundancy: Primary/Secondary available

### Example 2: Unlocked SNP Device
```prometheus
ic_snp_ptp_status{target="SNP-192.168.90.23"} 0.0
ic_snp_ptp_master_offset{target="SNP-192.168.90.23"} 0.0
ic_snp_ptp_master_delay{target="SNP-192.168.90.23"} 0.0
ic_snp_ptp_is_master{target="SNP-192.168.90.23"} 1.0
ic_snp_ptp_biggest_sys_time_update_ms{target="SNP-192.168.90.23"} 0.0
ic_snp_ptp_num_sys_time_updates{target="SNP-192.168.90.23"} 0.0
ic_snp_ptp_info{
  clock_identity="00 90 F9 FF FE 34 8F 40",
  controller_state="Unlocked-Free Run",
  master_ip="0.0.0.0",
  master_interface_ip="0.0.0.0",
  master_uuid="00-90-F9-FF-FE-34-8F-40",
  master_present="Primary/Secondary",
  utc_time="Fri Feb 6 05:13:47 2026",
  rtc_time="N/A",
  target="SNP-192.168.90.23"
} 1.0
```

**Interpretation:**
- ❌ Status: Unlocked-Free Run (problem)
- ⚠️ Offset: 0 (no master to sync with)
- ⚠️ Delay: 0 (no master)
- ⚠️ Role: Master (acting as own master - free run)
- ⚠️ Master IP: 0.0.0.0 (no master found)
- ❌ UTC Time: Feb 6 (wrong - should be Feb 3)
- **Action Required:** Configure PTP master or check network

---

## Benefits of Enhanced PTP Metrics

### Before Enhancement
- Basic lock status only
- Limited troubleshooting info
- No master identification
- No time accuracy tracking

### After Enhancement
- Complete PTP visibility
- Master failover tracking
- Time accuracy monitoring
- Network delay visibility
- Role identification (master/slave)
- Historical time adjustments
- Comprehensive alerting possible

---

## References

- SNP WebSocket Documentation: `SNP_Websocket.pdf`
- PTP Standard: IEEE 1588
- Prometheus Info Metric: https://prometheus.io/docs/concepts/metric_types/#info

---

**Feature Added:** 2026-02-03
**Metrics Count:** 7 (up from 3)
**Backwards Compatible:** Yes (existing metrics unchanged)
