# Processor Personality Feature

## Overview
Added automatic monitoring of SNP processor personalities (A, B, C, D) via periodic REST API polling.

## Implementation

### Metric Definition
```python
processor_personality = Info('ic_snp_processor_personality', 'Processor personality', ['target', 'processor'])
```

### REST API Endpoints Polled
For each SNP connection, the following endpoints are polled every 60 seconds:
- `/api/elements/{elementIp}/config/processorA`
- `/api/elements/{elementIp}/config/processorB`
- `/api/elements/{elementIp}/config/processorC`
- `/api/elements/{elementIp}/config/processorD`

### Data Extraction
From each processor config response:
```json
{
  "config": "{\"general\":{\"personality\":\"Multiviewer\",...},...}"
}
```

The personality field is extracted from `config.general.personality` and exposed as a Prometheus Info metric.

### Worker Architecture

Each SNP worker now runs two concurrent tasks:
1. **WebSocket Listener** (main thread) - Receives status updates
2. **Personality Poller** (background task) - Polls processor configs every 60 seconds

The personality task lifecycle:
- Started after WebSocket authentication succeeds
- Runs independently in background
- Cancelled automatically when WebSocket disconnects
- Restarted on reconnection

## Example Metrics Output

```prometheus
# HELP ic_snp_processor_personality_info Processor personality
# TYPE ic_snp_processor_personality_info gauge
ic_snp_processor_personality_info{personality="Multiviewer",processor="processorA",target="SNP-192.168.90.23"} 1.0
ic_snp_processor_personality_info{personality="Master Control Lite",processor="processorB",target="SNP-192.168.90.23"} 1.0
ic_snp_processor_personality_info{personality="Remap",processor="processorC",target="SNP-192.168.90.23"} 1.0
ic_snp_processor_personality_info{personality="Dual Gateway",processor="processorD",target="SNP-192.168.90.23"} 1.0
ic_snp_processor_personality_info{personality="JPEG-XS Encoder (TR-07)",processor="processorA",target="SNP-192.168.90.33"} 1.0
ic_snp_processor_personality_info{personality="Conv",processor="processorB",target="SNP-192.168.90.33"} 1.0
ic_snp_processor_personality_info{personality="Sync",processor="processorC",target="SNP-192.168.90.33"} 1.0
ic_snp_processor_personality_info{personality="Sync",processor="processorD",target="SNP-192.168.90.33"} 1.0
```

## Processor Personalities Discovered

Based on live SNP devices at 192.168.90.23 and 192.168.90.33:

### SNP-192.168.90.23
- **Processor A**: Multiviewer
- **Processor B**: Master Control Lite
- **Processor C**: Remap
- **Processor D**: Dual Gateway

### SNP-192.168.90.33
- **Processor A**: JPEG-XS Encoder (TR-07)
- **Processor B**: Conv (Converter)
- **Processor C**: Sync (Synchronizer)
- **Processor D**: Sync (Synchronizer)

## Common Personality Types

Based on observations:
- **Multiviewer** - Multi-image display processing
- **Master Control Lite** - MCL automation control
- **Remap** - Signal routing/remapping
- **Dual Gateway** - IP/SDI gateway
- **JPEG-XS Encoder (TR-07)** - Video compression
- **Conv** - Format conversion
- **Sync** - Frame synchronization
- **JPEG-XS Decoder (TR-07)** - Video decompression
- **Blank** - Unassigned/disabled processor

## Technical Details

### get_processor_personality Function
```python
async def get_processor_personality(name, base_url, token, element_ip, processor):
    api_base = base_url.rsplit('/api/', 1)[0]
    url = f"{api_base}/api/elements/{element_ip}/config/{processor}"
    
    resp = await session.get(url, headers={"Authorization": token})
    response_data = await resp.json()
    
    config = json.loads(response_data['config'])
    personality = config['general']['personality']
    
    return personality
```

### processor_personality_poller Task
```python
async def processor_personality_poller(name, url, username, password, element_ip):
    while True:
        await asyncio.sleep(60)  # Poll every 60 seconds
        
        token = await get_token(name, url, username, password)
        
        for processor in ['processorA', 'processorB', 'processorC', 'processorD']:
            personality = await get_processor_personality(name, url, token, element_ip, processor)
            if personality:
                processor_personality.labels(
                    target=name, 
                    processor=processor
                ).info({"personality": personality})
```

### Element IP Detection
The `elementIP` is automatically extracted from the first object in `objects_ids`:
```python
element_ip = "127.0.0.1"  # Default
if objects_ids and len(objects_ids) > 0:
    element_ip = objects_ids[0].get("elementIP", "127.0.0.1")
```

## Polling Interval

**60 seconds** - Processor personalities rarely change, so frequent polling isn't necessary.

### Why 60 seconds?
- Personalities are configuration, not real-time status
- Reduces REST API call load on SNP device
- Sufficient for alerting if personality changes
- Balances freshness vs overhead

## Error Handling

- Missing personality field → Logged and skipped
- REST API failure → Logged, continues polling
- Token failure → Skipped until next poll
- Task cancellation → Graceful shutdown on disconnect

## Use Cases

### Grafana Dashboards
Query processor personalities:
```promql
ic_snp_processor_personality_info{target="SNP-192.168.90.23"}
```

### Alerting
Detect personality changes:
```promql
changes(ic_snp_processor_personality_info[5m]) > 0
```

### Inventory
List all processor configurations across SNP fleet:
```promql
count by (personality) (ic_snp_processor_personality_info)
```

## Comparison with Original Code

### Original (JavaScript/Node.js)
```javascript
const proca = JSON.parse(res.data.config);
if (proca.general && proca.general.personality) {
    snpProcA.labels({
        personality: proca.general.personality
    }).set(1);
}
```

### New Implementation (Python/Async)
```python
personality = await get_processor_personality(name, url, token, element_ip, 'processorA')
if personality:
    processor_personality.labels(
        target=name, 
        processor='processorA'
    ).info({"personality": personality})
```

### Key Differences
- **Python**: Uses async/await with aiohttp
- **Labels**: Added `processor` label to differentiate A/B/C/D
- **Info Metric**: Uses Prometheus Info type instead of Gauge
- **Background Task**: Runs concurrently with WebSocket listener
- **Auto-cleanup**: Task cancelled when worker stops

## Testing Results

✅ REST API authentication works
✅ Processor configs fetched successfully
✅ Personalities extracted from JSON
✅ Metrics exposed in Prometheus format
✅ All 4 processors monitored per connection
✅ Background task runs every 60 seconds
✅ Task cleanup on disconnect works
✅ Multiple SNP devices supported

## Example Log Output

```
2026-02-03 20:54:35.676 INFO Worker SNP-192.168.90.23 processorA personality: Multiviewer
2026-02-03 20:54:35.723 INFO Worker SNP-192.168.90.23 processorB personality: Master Control Lite
2026-02-03 20:54:35.772 INFO Worker SNP-192.168.90.23 processorC personality: Remap
2026-02-03 20:54:35.817 INFO Worker SNP-192.168.90.23 processorD personality: Dual Gateway
```

## Files Modified

- **src/main.py**:
  - Added `processor_personality` Info metric (line ~60)
  - Added `get_processor_personality()` function (line ~406)
  - Added `processor_personality_poller()` background task (line ~208)
  - Modified `worker()` to start/stop personality poller (line ~234+)
  
- **README.md**:
  - Added processor metrics documentation
  - Documented polling interval

## Configuration

No additional configuration required. The feature automatically activates for all SNP connections.

The element IP is derived from the first `objects_ids` entry in each connection configuration.
