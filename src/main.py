import os
import logging
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import Info, Counter, Gauge, make_asgi_app, REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR
import asyncio
import aiohttp
import uvicorn
import websockets
import ssl
from websockets import serve
from typing import Dict, List
import database as db

logging.basicConfig(
  format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
  level=os.getenv("LOGGING", logging.INFO),
  datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "/etc/snp_exporter/connections.db")

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)

app = FastAPI(title="SNP Exporter Metrics")
ui_app = FastAPI(title="SNP Exporter UI")

templates = Jinja2Templates(directory="templates")

event = asyncio.Event()

api_status = Gauge('ic_snp_api_status', 'SNP Exporter API status', ['target'])
received_count = Counter('ic_snp_received_count', 'SNP WebSocket received messages', ['target'])
received_duration = Gauge('ic_snp_last_received_duration_seconds', 'SNP WebSocket last message duration seconds', ['target'])

temperature_mainboard = Gauge('ic_snp_mainboard_temperature', 'Main board temperature', ['target'])
temperature_ioboard = Gauge('ic_snp_ioboard_temperature', 'IO board temperature', ['target'])
powersupply_status = Gauge('ic_snp_powersupply_status', 'Power supply status (OK == 1)', ['target'])
hardware_stats = Info('ic_snp_hardware', 'Hardware Stats information', ['target'])
major_alarms = Gauge('ic_snp_major_alarms', 'Number of Major Alarms', ['target'])
minor_alarms = Gauge('ic_snp_minor_alarms', 'Number of Minor Alarms', ['target'])
fpga_temperature  = Gauge('ic_snp_fpga_temperature', 'FPGA temperature', ['target', 'index'])
fpga_fan_status  = Gauge('ic_snp_fpga_fan_status', 'FPGA fan status (OK == 1)', ['target', 'index'])
front_fan_status  = Gauge('ic_snp_front_fan_status', 'Front fan status (OK == 1)', ['target', 'index'])
qsfp_temperature  = Gauge('ic_snp_qsfp_temperature', 'QSFP temperature', ['target', 'index'])

ptp_status = Gauge('ic_snp_ptp_status', 'PTP status (1=Locked, 0=Not Locked)', ['target'])
ptp_master_offset = Gauge('ic_snp_ptp_master_offset', 'PTP master offset', ['target'])
ptp_master_delay = Gauge('ic_snp_ptp_master_delay', 'PTP master delay', ['target'])
ptp_info = Info('ic_snp_ptp_info', 'PTP information', ['target'])
ptp_biggest_sys_time_update = Gauge('ic_snp_ptp_biggest_sys_time_update_ms', 'Biggest system time update (milliseconds)', ['target'])
ptp_num_sys_time_updates = Gauge('ic_snp_ptp_num_sys_time_updates', 'Number of system time updates', ['target'])
ptp_is_master = Gauge('ic_snp_ptp_is_master', 'PTP is master (1=Master, 0=Slave)', ['target'])

video_rx = Info('ic_snp_video_rx', 'Video RX information', ['target', 'index'])

aco_abstatus = Gauge('ic_snp_aco_abstatus', 'ACO A/B Status', ['target', 'index'])

# Processor personality
processor_personality = Info('ic_snp_processor_personality', 'Processor personality', ['target', 'processor'])

# QSFP status metrics
qsfp_present = Gauge('ic_snp_qsfp_present', 'QSFP module present (1=Present, 0=Not Present)', ['target', 'index'])
qsfp_data_valid = Gauge('ic_snp_qsfp_data_valid', 'QSFP data valid (1=Valid, 0=Invalid)', ['target', 'index'])
qsfp_temp_alarm = Gauge('ic_snp_qsfp_temp_alarm', 'QSFP temperature alarm (1=Alarm, 0=OK)', ['target', 'index'])

# SFP status metrics
sfp_present = Gauge('ic_snp_sfp_present', 'SFP module present (1=Present, 0=Not Present)', ['target', 'index'])
sfp_mismatch = Gauge('ic_snp_sfp_mismatch', 'SFP module mismatch (1=Mismatch, 0=OK)', ['target', 'index'])

# FPGA alarm metrics
fpga_temp_alarm = Gauge('ic_snp_fpga_temp_alarm', 'FPGA temperature alarm (1=Alarm, 0=OK)', ['target', 'index'])
fpga_config_alarm = Gauge('ic_snp_fpga_config_alarm', 'FPGA configuration alarm (1=Alarm, 0=OK)', ['target', 'index'])
fpga_fan_alarm = Gauge('ic_snp_fpga_fan_alarm', 'FPGA fan alarm (1=Alarm, 0=OK)', ['target', 'index'])

# Fan RPM metrics
front_fan_rpm = Gauge('ic_snp_front_fan_rpm', 'Front fan rotational speed (RPM)', ['target', 'index'])

# FCS error metrics
fcs_primary_errors_exceeded = Gauge('ic_snp_fcs_primary_errors_exceeded', 'Primary FCS errors exceeded threshold (1=Yes, 0=No)', ['target'])
fcs_secondary_errors_exceeded = Gauge('ic_snp_fcs_secondary_errors_exceeded', 'Secondary FCS errors exceeded threshold (1=Yes, 0=No)', ['target'])

# Processor configuration metrics
processor_force_mab = Gauge('ic_snp_processor_force_mab', 'Force MAB mode enabled (1=Enabled, 0=Disabled)', ['target', 'processor'])
processor_audio_packet_time = Gauge('ic_snp_processor_audio_packet_time_ms', 'Audio IP TX packet time (milliseconds)', ['target', 'processor'])

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/-/reload")
async def reload():
    event.set()
    return Response("config reloaded")

@ui_app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@ui_app.get("/api/connections")
async def get_connections_api():
    try:
        connections = await db.get_connections()
        return JSONResponse(content=connections)
    except Exception as err:
        logger.error(f"Failed to get connections: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

@ui_app.get("/api/connections/{conn_id}")
async def get_connection_api(conn_id: int):
    try:
        connection = await db.get_connection_by_id(conn_id)
        if connection:
            return JSONResponse(content=connection)
        return JSONResponse(content={"error": "Connection not found"}, status_code=404)
    except Exception as err:
        logger.error(f"Failed to get connection {conn_id}: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

@ui_app.post("/api/connections")
async def add_connection_api(request: Request):
    try:
        data = await request.json()
        conn_id = await db.add_connection(data)
        event.set()
        return JSONResponse(content={"id": conn_id, "message": "Connection added"})
    except Exception as err:
        logger.error(f"Failed to add connection: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

@ui_app.put("/api/connections/{conn_id}")
async def update_connection_api(conn_id: int, request: Request):
    try:
        data = await request.json()
        success = await db.update_connection(conn_id, data)
        if success:
            event.set()
            return JSONResponse(content={"message": "Connection updated"})
        return JSONResponse(content={"error": "Connection not found"}, status_code=404)
    except Exception as err:
        logger.error(f"Failed to update connection {conn_id}: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

@ui_app.delete("/api/connections/{conn_id}")
async def delete_connection_api(conn_id: int):
    try:
        success = await db.delete_connection(conn_id)
        if success:
            event.set()
            return JSONResponse(content={"message": "Connection deleted"})
        return JSONResponse(content={"error": "Connection not found"}, status_code=404)
    except Exception as err:
        logger.error(f"Failed to delete connection {conn_id}: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

@ui_app.get("/api/export")
async def export_connections():
    try:
        connections = await db.get_connections()
        # Remove status fields and IDs for clean export
        export_data = []
        for conn in connections:
            export_data.append({
                "name": conn["name"],
                "restapi": conn["restapi"],
                "websocket": conn["websocket"],
                "username": conn["username"],
                "password": conn["password"],
                "objects_ids": conn["objects_ids"],
                "enabled": conn["enabled"]
            })
        return JSONResponse(content={
            "version": "1.0",
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "connections": export_data
        })
    except Exception as err:
        logger.error(f"Failed to export connections: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

@ui_app.post("/api/import")
async def import_connections(request: Request):
    try:
        data = await request.json()
        
        if "connections" not in data:
            return JSONResponse(content={"error": "Invalid import format: 'connections' key required"}, status_code=400)
        
        connections = data["connections"]
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for conn in connections:
            try:
                # Check if connection with same name already exists
                existing = await db.get_connection_by_name(conn["name"])
                if existing:
                    skipped_count += 1
                    errors.append(f"Connection '{conn['name']}' already exists, skipped")
                    continue
                
                # Validate required fields
                required_fields = ["name", "restapi", "websocket", "username", "password", "objects_ids"]
                if not all(field in conn for field in required_fields):
                    errors.append(f"Connection '{conn.get('name', 'unknown')}' missing required fields")
                    skipped_count += 1
                    continue
                
                # Add connection
                await db.add_connection(conn)
                imported_count += 1
                
            except Exception as err:
                errors.append(f"Failed to import '{conn.get('name', 'unknown')}': {str(err)}")
                skipped_count += 1
        
        # Trigger reload if any connections were imported
        if imported_count > 0:
            event.set()
        
        return JSONResponse(content={
            "message": "Import completed",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors
        })
        
    except Exception as err:
        logger.error(f"Failed to import connections: {err}")
        return JSONResponse(content={"error": str(err)}, status_code=500)

async def processor_personality_poller(name, url, username, password, element_ip):
    """Background task to poll processor personalities every 60 seconds"""
    while True:
        try:
            await asyncio.sleep(60)  # Poll every 60 seconds
            
            token = await get_token(name, url, username, password)
            if not token:
                continue
            
            # Poll all four processors
            for processor in ['processorA', 'processorB', 'processorC', 'processorD']:
                personality = await get_processor_personality(name, url, token, element_ip, processor)
                if personality:
                    processor_personality.labels(target=name, processor=processor).info({
                        "personality": personality
                    })
                    logger.info(f"Worker {name} {processor} personality: {personality}")
                    
        except asyncio.CancelledError:
            logger.info(f"Processor personality poller for {name} cancelled")
            raise
        except Exception as err:
            logger.error(f"Processor personality poller error for {name}: {err}")
            await asyncio.sleep(60)

async def worker(conn_id: int, interval: int):
    while True:
        conn = await db.get_connection_by_id(conn_id)
        if not conn or not conn["enabled"]:
            logger.info(f"Worker for connection {conn_id} disabled or deleted, exiting")
            return

        name = conn["name"]
        url = conn["restapi"]
        uri = conn["websocket"]
        username = conn["username"]
        password = conn["password"]
        objects_ids = conn["objects_ids"]
        
        # Extract element IP from objects_ids (use first one found, default to 127.0.0.1)
        element_ip = "127.0.0.1"
        if objects_ids and len(objects_ids) > 0:
            element_ip = objects_ids[0].get("elementIP", "127.0.0.1")

        await db.update_connection_status(conn_id, "connecting")

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            api_status.labels(target=name).set(0)
            async with websockets.connect(uri, ssl=ssl_context) as websocket:
                logger.info(f"Worker {name} websocket connected")

                token = await get_token(name, url, username, password)
                if not token:
                    await db.update_connection_status(conn_id, "error")
                    await asyncio.sleep(interval)
                    continue

                logger.info(f"Worker {name} sending authentication")
                await websocket.send(token)

                subscriptions = json.dumps(objects_ids)
                data = {"msgType":"statusListSubscribe","frequency":1000,"objectIds": objects_ids}
                message = json.dumps(data)
                logger.info(f"Worker {name} sending subscriptions: {message}")
                await websocket.send(message)

                await db.update_connection_status(conn_id, "connected")
                
                # Start processor personality poller task
                personality_task = asyncio.create_task(
                    processor_personality_poller(name, url, username, password, element_ip),
                    name=f"personality_{conn_id}"
                )

                try:
                    while True:
                        try:
                            message = await websocket.recv()
                            api_status.labels(target=name).set(1)
                            received_count.labels(target=name).inc()
                            await db.update_connection_status(conn_id, "connected")
                            
                            data = json.loads(message)
                            msg_type = data["msgType"]
                            logger.info(f"Worker {name} received message type: {msg_type}")

                            if (msg_type == "fmmStatus"
                            or  msg_type == "permissionMessage"
                            or  msg_type == "logState"):
                                pass
                            
                            elif (msg_type == "activeAlarmStatus"):
                                logger.info(f"Worker {name} alarm status message: {data}")

                            elif (msg_type == "statusState"
                            or    msg_type == "allStatuses"):
                                logger.debug(f"Worker {name} status message: {data}")

                                start_time = time.time()

                                parsed_list = [json.loads(item) for item in data["statuses"]]
                                await parse_statuses(parsed_list, name)

                                end_time = time.time()
                                received_duration.labels(target=name).set(end_time - start_time)

                            else:
                                logger.debug(f"Worker {name} message type {msg_type} is not yet implemented: {data}")

                            if subscriptions != json.dumps(objects_ids):
                                logger.info(f"Worker {name} has new subscriptions, need to resubscribe.")
                                break

                            await asyncio.sleep(interval)

                        except websockets.exceptions.ConnectionClosed:
                            api_status.labels(target=name).set(0.0)
                            await db.update_connection_status(conn_id, "disconnected")
                            logger.error(f"Worker {name} disconnected, retrying...")
                            await asyncio.sleep(3 * interval)
                            break

                        except Exception as err:
                            logger.error(f"Worker {name} unexpected error: {err}")
                
                finally:
                    # Cancel personality task when exiting websocket
                    personality_task.cancel()
                    try:
                        await personality_task
                    except asyncio.CancelledError:
                        pass

        except ConnectionRefusedError:
            api_status.labels(target=name).set(0.0)
            await db.update_connection_status(conn_id, "error")
            logger.error(f"Worker {name} connection refused")
            await asyncio.sleep(interval)

        except websockets.exceptions.InvalidURI:
            api_status.labels(target=name).set(0.0)
            await db.update_connection_status(conn_id, "error")
            logger.error(f"Worker {name} invalid URI")
            await asyncio.sleep(interval)

        except Exception as err:
            api_status.labels(target=name).set(0.0)
            await db.update_connection_status(conn_id, "error")
            logger.error(f"Worker {name} unexpected error: {err}")
            await asyncio.sleep(interval)

def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return float('nan')

async def parse_statuses(statuses, name):
    for status in statuses:
        status_type = status["type"]
        if status_type == "system":
            hardware_stats.labels(target=name).info({
                "firmware": status["SNP_HW_Stats"]["FWRev"],
                "hardware": status["SNP_HW_Stats"]["HWRev"],
                "serial": status["SNP_HW_Stats"]["Serial"]
            })
            major_alarms.labels(target=name).set(status["Alarm_Stats"]["majorInstances"])
            minor_alarms.labels(target=name).set(status["Alarm_Stats"]["minorInstances"])
            temperature_mainboard.labels(target=name).set(safe_float(status["Board_Temperatures"]["Main_Board"].split(" ")[0]))
            temperature_ioboard.labels(target=name).set(safe_float(status["Board_Temperatures"]["IO_Board"].split(" ")[0]))
            powersupply_status.labels(target=name).set(1 if status["Power_Supply_Stats"]["PS_Status"] == "OK" else 0)
            # FPGA stats with alarms
            for stat in status["FPGA_HW_Stats"]:
                idx = stat["idx"]
                fpga_temperature.labels(target=name, index=idx).set(safe_float(stat["Temp"].split(" ")[0]))
                fpga_fan_status.labels(target=name, index=idx).set(1 if stat["Fan_Status"] == "OK" else 0)
                fpga_temp_alarm.labels(target=name, index=idx).set(1 if stat.get("Temp_Alarm", False) else 0)
                fpga_config_alarm.labels(target=name, index=idx).set(1 if stat.get("Configuration_Alarm", False) else 0)
                fpga_fan_alarm.labels(target=name, index=idx).set(1 if stat.get("Fan_Alarm", False) else 0)
            
            # Front fan stats with RPM
            for stat in status["Front_Fan_Stats"]:
                idx = stat["idx"]
                front_fan_status.labels(target=name, index=idx).set(1 if stat["Status"] == "OK" else 0)
                # Extract RPM from "11843 RPM" format
                rpm_str = stat.get("RotationalSpeed", "0 RPM").split(" ")[0]
                front_fan_rpm.labels(target=name, index=idx).set(safe_float(rpm_str))
            
            # QSFP stats with status
            for stat in status["QSFP_Stats"]:
                idx = stat["idx"]
                qsfp_temperature.labels(target=name, index=idx).set(safe_float(stat["Temperature"].split(" ")[0]))
                qsfp_present.labels(target=name, index=idx).set(1 if stat.get("present", False) else 0)
                qsfp_data_valid.labels(target=name, index=idx).set(1 if stat.get("dataValid", False) else 0)
                qsfp_temp_alarm.labels(target=name, index=idx).set(1 if stat.get("Temp_Alarm", False) else 0)
            
            # SFP stats
            for stat in status.get("SFP_Stats", []):
                idx = stat["idx"]
                sfp_present.labels(target=name, index=idx).set(1 if stat.get("SFP_Present", False) else 0)
                sfp_mismatch.labels(target=name, index=idx).set(1 if stat.get("SFP_Mismatch", False) else 0)
            
            # FCS error stats
            fcs_stats = status.get("FCS_Stats", {})
            fcs_primary_errors_exceeded.labels(target=name).set(1 if fcs_stats.get("priFCSerrorsExceeded", False) else 0)
            fcs_secondary_errors_exceeded.labels(target=name).set(1 if fcs_stats.get("secFCSerrorsExceeded", False) else 0)
        
        elif status_type == "ptp":
            ptp_data = status["ptpStatus"]
            
            # Existing metrics (backwards compatible)
            ptp_status.labels(target=name).set(1 if ptp_data["ptpCtlrState"] == "Locked" else 0)
            ptp_master_offset.labels(target=name).set(safe_float(ptp_data["ptpMasterOffset"].split(" ")[0]))
            ptp_master_delay.labels(target=name).set(safe_float(ptp_data["ptpMasterDelay"].split(" ")[0]))
            
            # New comprehensive PTP info
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
            
            # Numeric metrics
            biggest_update = ptp_data.get("biggestSysTimeUpdate", "0 ms").split(" ")[0]
            ptp_biggest_sys_time_update.labels(target=name).set(safe_float(biggest_update))
            
            num_updates = ptp_data.get("numSysTimeUpdates", "0")
            ptp_num_sys_time_updates.labels(target=name).set(safe_float(num_updates))
            
            # Is master or slave
            is_master_str = ptp_data.get("ptpUcipIsMaster", "Slave")
            ptp_is_master.labels(target=name).set(1 if is_master_str == "Master" else 0)

        elif status_type == "ipVidRx":
            for stat in status["ipVidRxStatus"]:
                video_rx.labels(target=name, index=stat["idx"]).info({"video": stat["VidRxStd"],
                                             "colorimetry": stat["VidRxColorimetry"]})
        elif status_type == "procChannelHD":
            aco_abstatus.labels(target=name, index=status["object_ID"]).set(1 if status["ACO"]["ABStatus"] == "A" else 0)

        else:
            logger.error(f"Worker {name} status type {status_type} is not yet implemented: {json.dumps(status)}")

async def get_token(name, url, username, password):
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
    headers = {"Content-type": "application/json"}
    data = {"username": username, "password": password}

    try:
        resp = await session.post(url, json=data, headers=headers)
        if resp.status in [200, 201, 204]:
            data = await resp.text()
            logger.debug(f"Worker {name} got token {data}")
            await session.close()
            return data
        else:
            data = await resp.text()
            logger.error(f"Worker {name} unable to get auth because: {data}")
            await session.close()
            return None

    except Exception as err:
        logger.error(f"Worker {name} unable to get token because: {err}")
        await session.close()
        return None

async def get_processor_personality(name, base_url, token, element_ip, processor):
    """Fetch processor personality and configuration from REST API"""
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        headers = {"Content-type": "application/json", "Authorization": token}
        
        # Extract base URL (remove /api/auth part)
        api_base = base_url.rsplit('/api/', 1)[0]
        url = f"{api_base}/api/elements/{element_ip}/config/{processor}"
        
        try:
            resp = await session.get(url, headers=headers)
            if resp.status in [200, 201, 204]:
                response_data = await resp.json()
                
                if 'config' in response_data:
                    config = json.loads(response_data['config'])
                    general = config.get('general', {})
                    
                    # Extract personality
                    personality = None
                    if 'personality' in general:
                        personality = general['personality']
                        logger.debug(f"Worker {name} {processor} personality: {personality}")
                    
                    # Extract additional config metrics
                    force_mab = 1 if general.get('forceMAB', False) else 0
                    audio_packet_time = safe_float(general.get('audioPacketTime', 0))
                    
                    # Update processor metrics
                    processor_force_mab.labels(target=name, processor=processor).set(force_mab)
                    processor_audio_packet_time.labels(target=name, processor=processor).set(audio_packet_time)
                    
                    logger.debug(f"Worker {name} {processor} forceMAB={force_mab}, audioPacketTime={audio_packet_time}ms")
                    
                    return personality
                
                logger.debug(f"Worker {name} {processor} no config found in response")
                return None
            else:
                error_text = await resp.text()
                logger.error(f"Worker {name} unable to get {processor} config: {error_text}")
                return None

        except Exception as err:
            logger.error(f"Worker {name} unable to get {processor} config: {err}")
            return None

def remove_metrics(target):
    try:
        api_status.remove(target)
        received_count.remove(target)
        received_duration.remove(target)
        temperature_mainboard.remove(target)
        temperature_ioboard.remove(target)
        powersupply_status.remove(target)
        ptp_status.remove(target)
        ptp_master_offset.remove(target)
        ptp_master_delay.remove(target)
        hardware_stats.remove(target)
        major_alarms.remove(target)
        minor_alarms.remove(target)
    except Exception as err:
        logger.error(f"Failed to remove metrics for target {target} because: {err}")

async def reloader(group, interval, poll_interval):
    active_connections: Dict[int, asyncio.Task] = {}
    connection_data: Dict[int, str] = {}

    while True:
        await event.wait()

        try:
            connections = await db.get_enabled_connections()
            current_ids = set(conn["id"] for conn in connections)
            active_ids = set(active_connections.keys())

            new_ids = current_ids - active_ids
            removed_ids = active_ids - current_ids

            for conn_id in removed_ids:
                logger.info(f"Stopping worker for connection {conn_id}")
                task = active_connections.get(conn_id)
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    del active_connections[conn_id]
                name = connection_data.get(conn_id)
                if name:
                    remove_metrics(name)
                    del connection_data[conn_id]

            for conn_id in new_ids:
                conn = next((c for c in connections if c["id"] == conn_id), None)
                if conn:
                    logger.info(f"Starting worker for connection {conn_id} ({conn['name']})")
                    connection_data[conn_id] = conn["name"]
                    task = group.create_task(worker(conn_id, interval), name=f"worker_{conn_id}")
                    active_connections[conn_id] = task

            for conn in connections:
                conn_id = conn["id"]
                old_name = connection_data.get(conn_id)
                if old_name and old_name != conn["name"]:
                    logger.info(f"Connection {conn_id} name or config changed, restarting")
                    connection_data[conn_id] = conn["name"]
                    task = active_connections.get(conn_id)
                    if task:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                        new_task = group.create_task(worker(conn_id, interval), name=f"worker_{conn_id}")
                        active_connections[conn_id] = new_task

        except Exception as err:
            logger.error(f"Reloader error: {err}")

        event.clear()
        await asyncio.sleep(poll_interval)
        event.set()

async def main():
    await db.init_db()

    metrics_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    metrics_server = uvicorn.Server(metrics_config)

    ui_config = uvicorn.Config(ui_app, host="0.0.0.0", port=8080, log_level="info")
    ui_server = uvicorn.Server(ui_config)

    interval = int(os.getenv("INTERVAL", 5))
    poll_interval = int(os.getenv("POLL_INTERVAL", 10))

    async with asyncio.TaskGroup() as tg:
        logger.info("Starting Uvicorn FastAPI metrics server on port 8000")
        tg.create_task(metrics_server.serve(), name="metrics")

        logger.info("Starting Uvicorn FastAPI UI server on port 8080")
        tg.create_task(ui_server.serve(), name="ui")

        logger.info("Starting reloader task")
        event.set()
        tg.create_task(reloader(tg, interval, poll_interval), name="reloader")

if __name__ == "__main__":
    asyncio.run(main())
