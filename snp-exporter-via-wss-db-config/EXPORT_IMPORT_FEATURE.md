# Export/Import Configuration Feature

## Overview
Added export and import functionality to allow users to backup, migrate, and restore SNP connection configurations via JSON files.

## Features

### Export Configuration
Downloads all connection configurations as a JSON file.

**UI Elements:**
- Green "Export" button with download icon
- Location: Top toolbar, left of Import button
- Tooltip: "Export all connections to JSON file"

**Functionality:**
- Exports all connections (regardless of enabled/disabled state)
- Excludes internal fields (id, status, timestamps)
- Includes credentials (for backup/restore purposes)
- Auto-downloads file with date-stamped name: `snp-connections-YYYY-MM-DD.json`
- Shows success notification with connection count

**Export Format:**
```json
{
    "version": "1.0",
    "exported_at": "2026-02-03 20:28:21",
    "connections": [
        {
            "name": "SNP-192.168.90.23",
            "restapi": "https://192.168.90.23:9089/api/auth",
            "websocket": "wss://192.168.90.23/smm",
            "username": "admin",
            "password": "password",
            "objects_ids": [
                {
                    "elementIP": "127.0.0.1",
                    "objectType": "ptp"
                }
            ],
            "enabled": true
        }
    ]
}
```

### Import Configuration
Restores connections from a previously exported JSON file.

**UI Elements:**
- Cyan "Import" button with upload icon
- Location: Top toolbar, between Export and Reload Config buttons
- Tooltip: "Import connections from JSON file"
- Hidden file input (triggered by Import button)

**Functionality:**
- Accepts JSON files with "connections" array
- Validates file format before processing
- Shows confirmation dialog with connection count
- Checks for duplicate names (skips existing)
- Validates required fields per connection
- Triggers automatic worker restart for imported connections
- Shows detailed summary: imported/skipped/errors
- Displays errors in browser console for troubleshooting

**Import Behavior:**
- **Duplicate Names**: Skipped with notification
- **Missing Fields**: Skipped with error message
- **Invalid Format**: Rejected with alert
- **Successful Import**: Workers start automatically

**Required Fields:**
- name (unique)
- restapi
- websocket
- username
- password
- objects_ids (array)

**Optional Fields:**
- enabled (defaults to true)

## API Endpoints

### GET /api/export
Returns all connections in export format.

**Response:**
```json
{
    "version": "1.0",
    "exported_at": "2026-02-03 20:28:21",
    "connections": [...]
}
```

**Status Codes:**
- 200: Success
- 500: Server error

### POST /api/import
Imports connections from JSON payload.

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
    "imported": 1,
    "skipped": 1,
    "errors": [
        "Connection 'SNP-192.168.90.23' already exists, skipped"
    ]
}
```

**Status Codes:**
- 200: Success (may have skipped items)
- 400: Invalid format
- 500: Server error

## User Flow

### Exporting Configuration

1. User clicks "Export" button
2. JavaScript calls `/api/export`
3. Backend queries all connections from database
4. Returns JSON with cleaned data (no IDs/status)
5. Browser downloads file automatically
6. Success notification displays: "Exported X connection(s) successfully."

### Importing Configuration

1. User clicks "Import" button
2. File picker opens (accepts .json only)
3. User selects previously exported JSON file
4. JavaScript reads file and validates format
5. Confirmation dialog shows: "Import X connection(s)?"
6. User confirms
7. JavaScript posts to `/api/import`
8. Backend:
   - Validates each connection
   - Checks for duplicates
   - Inserts new connections
   - Triggers config reload (event.set())
9. Success notification shows: "Imported: X, Skipped: Y"
10. Connection list refreshes
11. Workers start for new connections

## Implementation Details

### Backend (main.py)

**Export Endpoint:**
```python
@ui_app.get("/api/export")
async def export_connections():
    connections = await db.get_connections()
    export_data = []
    for conn in connections:
        export_data.append({
            "name": conn["name"],
            "restapi": conn["restapi"],
            # ... other fields
        })
    return JSONResponse(content={
        "version": "1.0",
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "connections": export_data
    })
```

**Import Endpoint:**
```python
@ui_app.post("/api/import")
async def import_connections(request: Request):
    data = await request.json()
    
    for conn in data["connections"]:
        # Check duplicates
        existing = await db.get_connection_by_name(conn["name"])
        if existing:
            skipped_count += 1
            continue
        
        # Validate and add
        await db.add_connection(conn)
        imported_count += 1
    
    # Trigger reload
    if imported_count > 0:
        event.set()
    
    return response with summary
```

### Frontend (index.html)

**Export Function:**
```javascript
async function exportConfig() {
    const response = await fetch('/api/export');
    const data = await response.json();
    
    // Create download
    const blob = new Blob([JSON.stringify(data, null, 2)], 
                         { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `snp-connections-${date}.json`;
    a.click();
}
```

**Import Function:**
```javascript
async function importConfig(event) {
    const file = event.target.files[0];
    const text = await file.text();
    const data = JSON.parse(text);
    
    // Validate
    if (!data.connections || !Array.isArray(data.connections)) {
        alert('Invalid format');
        return;
    }
    
    // Confirm
    if (!confirm(`Import ${data.connections.length} connection(s)?`)) {
        return;
    }
    
    // Import
    const response = await fetch('/api/import', {
        method: 'POST',
        body: text
    });
    
    const result = await response.json();
    showImportAlert(message);
    loadConnections();
}
```

### Database (database.py)

**New Function:**
```python
async def get_connection_by_name(name: str) -> Optional[Dict]:
    # Check if connection with name exists
    cursor = await conn.execute(
        "SELECT * FROM snp_connections WHERE name = ?", (name,)
    )
    return row or None
```

## Use Cases

### 1. Backup Before Major Changes
- Export current config
- Make changes via UI
- If issues occur, import backup to restore

### 2. Migration to New Server
- Export from old server
- Copy JSON file to new server
- Import on new server
- All connections restored with workers

### 3. Bulk Configuration
- Create JSON file manually or via script
- Import multiple connections at once
- Faster than adding one-by-one via UI

### 4. Configuration Templates
- Export a "template" configuration
- Modify JSON for different environments
- Import customized versions

### 5. Disaster Recovery
- Regular exports for backup
- Store JSON files externally
- Quick restore after data loss

## Security Considerations

**Credentials in Export:**
- Passwords are included in plaintext
- JSON file should be stored securely
- Consider encrypting export files for storage
- Restrict file access permissions

**Import Validation:**
- All fields validated before insert
- Duplicate names are rejected
- Invalid formats are rejected
- SQL injection prevented by parameterized queries

## Testing

### Export Test
```bash
# Via API
curl http://localhost:8080/api/export > backup.json

# Via UI
Click "Export" button → File downloads automatically
```

### Import Test
```bash
# Via API
curl -X POST http://localhost:8080/api/import \
  -H "Content-Type: application/json" \
  -d @backup.json

# Via UI
Click "Import" button → Select JSON file → Confirm
```

### Test Results
✅ Export returns valid JSON with all connections
✅ Import validates format correctly
✅ Duplicate names are skipped
✅ New connections are imported
✅ Workers start automatically after import
✅ Success notifications display correctly
✅ File downloads with correct filename

## Error Handling

**Export Errors:**
- Database query failure → 500 error
- No connections → Empty array (valid)

**Import Errors:**
- Invalid JSON format → Alert to user
- Missing "connections" key → 400 error
- Duplicate name → Skip with notification
- Missing required fields → Skip with error
- Database insert failure → Skip with error

**All errors logged to:**
- Backend: Application logs
- Frontend: Browser console

## Future Enhancements

Potential improvements:
- Password encryption in export files
- Selective export (choose specific connections)
- Import preview before confirmation
- Merge mode (update existing connections)
- Export/import filters (by enabled status)
- Scheduled automatic exports
- Cloud storage integration
