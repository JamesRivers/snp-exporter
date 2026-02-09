# Reload Config Button Feature

## Overview
Added a "Reload Config" button to the web UI that allows users to manually trigger configuration reloads and worker restarts.

## Feature Details

### UI Components

1. **Reload Config Button**
   - Location: Top right of the page, next to "Add Connection" button
   - Style: Secondary button with refresh icon (arrow-clockwise SVG)
   - Tooltip: "Reload configuration and restart workers"

2. **Success Alert**
   - Displays at top of page after reload triggered
   - Auto-dismisses after 3 seconds
   - Green success alert with message: "Config Reloaded! Workers are restarting with new configuration."

### Functionality

**Manual Reload:**
- User clicks "Reload Config" button
- JavaScript calls `http://host:8000/-/reload` endpoint
- Triggers immediate configuration check
- Shows success notification
- Refreshes connection list after 2 seconds

**Automatic Notifications:**
- Shows reload alert when connection is added
- Shows reload alert when connection is updated
- Shows reload alert when connection is deleted
- Informs user that workers are restarting with new config

### Behavior

1. **Reload Trigger:**
   ```javascript
   async function reloadConfig() {
       const metricsUrl = window.location.origin.replace(':8080', ':8000');
       const response = await fetch(`${metricsUrl}/-/reload`);
       if (response.ok) {
           showReloadAlert();
           setTimeout(loadConnections, 2000);
       }
   }
   ```

2. **Alert Display:**
   ```javascript
   function showReloadAlert() {
       const alert = document.getElementById('reloadAlert');
       alert.classList.add('show');
       setTimeout(() => {
           alert.classList.remove('show');
       }, 3000);
   }
   ```

3. **Integration with CRUD Operations:**
   - Add Connection → Shows alert automatically
   - Edit Connection → Shows alert automatically
   - Delete Connection → Shows alert automatically

### Backend Integration

The reload button calls the existing `/-/reload` endpoint on port 8000:
```python
@app.get("/-/reload")
async def reload():
    event.set()
    return Response("config reloaded")
```

This triggers the reloader task which:
1. Queries database for enabled connections
2. Compares with active workers
3. Starts new workers
4. Stops removed workers
5. Restarts modified workers

### User Experience

**Before:**
- Users had to wait up to 10 seconds for automatic reload
- No feedback that configuration was being applied
- Manual API call required for immediate reload

**After:**
- Instant reload on button click
- Visual feedback with success notification
- Automatic notifications on add/edit/delete operations
- Clear indication that workers are restarting

### UI Layout

```
┌──────────────────────────────────────────────────────────┐
│  SNP Connections      [Reload Config] [Add Connection]   │
│                                                           │
│  [✓ Config Reloaded! Workers are restarting... ×]       │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ID │ Name │ WebSocket │ Status │ Last Update │ ... │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Testing

1. **Manual Reload Test:**
   ```bash
   # Start container
   docker compose up -d
   
   # Access UI
   open http://localhost:8080/
   
   # Click "Reload Config" button
   # Should see green success alert
   # Workers should restart in logs
   ```

2. **Add Connection Test:**
   ```bash
   # Click "Add Connection"
   # Fill in form
   # Click "Save"
   # Should see success alert automatically
   ```

3. **API Test:**
   ```bash
   curl http://localhost:8000/-/reload
   # Should return: "config reloaded"
   
   # Check logs
   docker logs observe-snpexporter
   # Should show workers restarting
   ```

## Implementation Files

### Modified Files:
- `src/templates/index.html`:
  - Added reload button with SVG icon
  - Added `reloadAlert` div
  - Added `reloadConfig()` function
  - Added `showReloadAlert()` function
  - Integrated alert into save/delete operations

### Code Changes:
1. Button HTML (line ~29-40)
2. Alert div (line ~41-45)
3. JavaScript functions (line ~428-442)
4. Integration in saveConnection (line ~366)
5. Integration in confirmDelete (line ~415)

## Benefits

1. **Immediate Feedback**: Users know their changes are being applied
2. **Manual Control**: Option to force reload without waiting
3. **Visual Confirmation**: Green alert shows successful reload
4. **Better UX**: Clear communication of system state
5. **No Breaking Changes**: Existing auto-reload still works

## Notes

- The 10-second automatic reload still functions normally
- Manual reload is useful when immediate worker restart is needed
- Alert is non-intrusive (auto-dismisses after 3 seconds)
- Button has tooltip explaining its purpose
- Cross-origin fetch works because both ports are on same host
