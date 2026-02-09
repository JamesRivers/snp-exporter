import os
import aiosqlite
import logging
import json
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "/etc/snp_exporter/connections.db")

async def init_db():
    await create_tables()
    logger.info("Database initialized")

async def get_db_connection():
    return await aiosqlite.connect(DB_PATH)

async def create_tables():
    conn = await get_db_connection()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS snp_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            restapi TEXT NOT NULL,
            websocket TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            objects_ids TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS connection_status (
            connection_id INTEGER PRIMARY KEY,
            status TEXT NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connection_id) REFERENCES snp_connections(id) ON DELETE CASCADE
        )
    """)
    await conn.commit()
    await conn.close()

async def get_connections() -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    conn.row_factory = aiosqlite.Row
    cursor = await conn.execute("""
        SELECT c.*, s.status, s.last_update
        FROM snp_connections c
        LEFT JOIN connection_status s ON c.id = s.connection_id
        ORDER BY c.id
    """)
    rows = await cursor.fetchall()
    await conn.close()
    
    connections = []
    for row in rows:
        connections.append({
            "id": row["id"],
            "name": row["name"],
            "restapi": row["restapi"],
            "websocket": row["websocket"],
            "username": row["username"],
            "password": row["password"],
            "objects_ids": json.loads(row["objects_ids"]),
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "status": row["status"] or "disconnected",
            "last_update": row["last_update"]
        })
    return connections

async def get_connection_by_id(conn_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_db_connection()
    conn.row_factory = aiosqlite.Row
    cursor = await conn.execute("""
        SELECT * FROM snp_connections WHERE id = ?
    """, (conn_id,))
    row = await cursor.fetchone()
    await conn.close()
    
    if row:
        return {
            "id": row["id"],
            "name": row["name"],
            "restapi": row["restapi"],
            "websocket": row["websocket"],
            "username": row["username"],
            "password": row["password"],
            "objects_ids": json.loads(row["objects_ids"]),
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    return None

async def get_connection_by_name(name: str) -> Optional[Dict[str, Any]]:
    conn = await get_db_connection()
    conn.row_factory = aiosqlite.Row
    cursor = await conn.execute("""
        SELECT * FROM snp_connections WHERE name = ?
    """, (name,))
    row = await cursor.fetchone()
    await conn.close()
    
    if row:
        return {
            "id": row["id"],
            "name": row["name"],
            "restapi": row["restapi"],
            "websocket": row["websocket"],
            "username": row["username"],
            "password": row["password"],
            "objects_ids": json.loads(row["objects_ids"]),
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    return None

async def add_connection(data: Dict[str, Any]) -> int:
    conn = await get_db_connection()
    cursor = await conn.execute("""
        INSERT INTO snp_connections (name, restapi, websocket, username, password, objects_ids, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["restapi"],
        data["websocket"],
        data["username"],
        data["password"],
        json.dumps(data["objects_ids"]),
        int(data.get("enabled", True))
    ))
    conn_id = cursor.lastrowid
    await conn.commit()
    await conn.close()
    return conn_id

async def update_connection(conn_id: int, data: Dict[str, Any]) -> bool:
    conn = await get_db_connection()
    fields = []
    values = []
    
    for field in ["name", "restapi", "websocket", "username", "password", "objects_ids", "enabled"]:
        if field in data:
            if field == "objects_ids":
                fields.append(f"{field} = ?")
                values.append(json.dumps(data[field]))
            elif field == "enabled":
                fields.append(f"{field} = ?")
                values.append(int(data[field]))
            else:
                fields.append(f"{field} = ?")
                values.append(data[field])
    
    if not fields:
        await conn.close()
        return False
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(conn_id)
    
    query = f"UPDATE snp_connections SET {', '.join(fields)} WHERE id = ?"
    cursor = await conn.execute(query, values)
    await conn.commit()
    affected = cursor.rowcount
    await conn.close()
    return affected > 0

async def delete_connection(conn_id: int) -> bool:
    conn = await get_db_connection()
    cursor = await conn.execute("DELETE FROM snp_connections WHERE id = ?", (conn_id,))
    await conn.commit()
    affected = cursor.rowcount
    await conn.close()
    return affected > 0

async def update_connection_status(conn_id: int, status: str) -> bool:
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT OR REPLACE INTO connection_status (connection_id, status, last_update)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (conn_id, status))
        await conn.commit()
        await conn.close()
        return True
    except Exception as err:
        logger.error(f"Failed to update status for connection {conn_id}: {err}")
        await conn.close()
        return False

async def get_connection_status(conn_id: int) -> Optional[str]:
    conn = await get_db_connection()
    cursor = await conn.execute("""
        SELECT status FROM connection_status WHERE connection_id = ?
    """, (conn_id,))
    row = await cursor.fetchone()
    await conn.close()
    
    if row:
        return row[0]
    return "disconnected"

async def get_enabled_connections() -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    conn.row_factory = aiosqlite.Row
    cursor = await conn.execute("""
        SELECT * FROM snp_connections WHERE enabled = 1 ORDER BY id
    """)
    rows = await cursor.fetchall()
    await conn.close()
    
    connections = []
    for row in rows:
        connections.append({
            "id": row["id"],
            "name": row["name"],
            "restapi": row["restapi"],
            "websocket": row["websocket"],
            "username": row["username"],
            "password": row["password"],
            "objects_ids": json.loads(row["objects_ids"]),
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    return connections
