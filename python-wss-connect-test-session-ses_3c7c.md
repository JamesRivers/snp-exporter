# Websocket JWT Authentication and keepalive protocol

**Session ID:** ses_3c7c20c14ffeN0WhmbaP8H91c5
**Created:** 2/7/2026, 1:15:10 PM
**Updated:** 2/7/2026, 1:17:43 PM

---

## User

Establishing the Websocket Connection and Security
URL: wss://<address_of_smm>/smm
The interface is secured using WSS (secure websocket protocol) and permissions are established using
the same authentication tokens that are used on the REST API. In the HTTPS case, this bearer token (a
JWT) is normally put into the header of each REST API request, however for our websocket protocol, it is
simply furnished as the contents of the first message.
String apiBase = "https://137.237.176.76:9089/api/";
JsonObjectBuilder userAuth = Json.createObjectBuilder();
userAuth.add("username", "admin");
userAuth.add("password", "password");
HTTPResponse res = postJsonObject_rr(apiBase+"auth", userAuth.build());
String jwtAuthToken = res.getResponse();
This token is sent as the first message after successfully connecting on the websocket.
String wsAddr = "wss://137.237.176.76/smm";
WSClient webSock = null;
webSock = new WSClient(new URI(wsAddr));
webSock.configSecurityLite();
Boolean success = webSock.connectBlocking();
webSock.sendMessage(jwtAuthToken);
After connecting and sending the JWT, the websocket is ready for use. “fmmStatus” keep-alive
messages are sent periodically by the server.
{"msgType":"fmmStatus","event":"keepalive","status":"success","description":"30-03-2021
00:18:43","managed_services":0,"available_services":0} 

---

## Assistant (Build · claude-sonnet-4-5 · 6.7s)

I can see you've shared documentation about establishing a WebSocket connection to an SMM (Service Management Module) with security authentication. This describes a two-step authentication process:

1. **Get JWT token via REST API** - POST to `/api/auth` with username/password
2. **Connect to WebSocket** - Send the JWT as the first message after connection

Is there something specific you'd like me to help you with regarding this WebSocket connection? For example:

- Implement a client that connects to this SMM WebSocket?
- Debug an existing implementation?
- Add this functionality to the current codebase?
- Create tests for WebSocket authentication?
- Something else?

Let me know what you need, and I'll be happy to assist!

---

## User

build a pythin script that connects to an SNP, via the WSS and then gets all data via this type of command - Clients can request specific classes of information on the websocket. For example sending:
"{"msgType":"getAllObjects", "elementIp":"137.237.176.76"}");  save the python script and save the return data in a friendly format to read

---

## Assistant (Build · claude-sonnet-4-5 · 4.7s)

I'll create a Python script that connects to the SNP via WebSocket, authenticates, and retrieves data. Let me build this for you.

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "id": "1",
      "content": "Create Python WebSocket client script for SNP connection",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Implement authentication flow (REST API + JWT)",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Implement WebSocket connection and message handling",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Add data retrieval via getAllObjects command",
      "status": "pending",
      "priority": "high"
    },
    {
      "id": "5",
      "content": "Save received data in readable format (JSON)",
      "status": "pending",
      "priority": "medium"
    }
  ]
}
```

**Output:**
```
[
  {
    "id": "1",
    "content": "Create Python WebSocket client script for SNP connection",
    "status": "in_progress",
    "priority": "high"
  },
  {
    "id": "2",
    "content": "Implement authentication flow (REST API + JWT)",
    "status": "pending",
    "priority": "high"
  },
  {
    "id": "3",
    "content": "Implement WebSocket connection and message handling",
    "status": "pending",
    "priority": "high"
  },
  {
    "id": "4",
    "content": "Add data retrieval via getAllObjects command",
    "status": "pending",
    "priority": "high"
  },
  {
    "id": "5",
    "content": "Save received data in readable format (JSON)",
    "status": "pending",
    "priority": "medium"
  }
]
```

---

## Assistant (Build · claude-sonnet-4-5 · 37.7s)

**Tool: write**

**Input:**
```json
{
  "filePath": "/home/imagine/snp-exporter/snp_websocket_client.py",
  "content": "#!/usr/bin/env python3\n\"\"\"\nSNP WebSocket Client\nConnects to SNP via secure WebSocket, authenticates, and retrieves data.\n\"\"\"\n\nimport asyncio\nimport websockets\nimport json\nimport requests\nimport ssl\nimport sys\nfrom datetime import datetime\nfrom pathlib import Path\nimport urllib3\n\n# Disable SSL warnings for self-signed certificates\nurllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)\n\n\nclass SNPWebSocketClient:\n    \"\"\"Client for connecting to SNP via WebSocket and retrieving data.\"\"\"\n    \n    def __init__(self, host, port=9089, username=\"admin\", password=\"password\"):\n        \"\"\"\n        Initialize the SNP WebSocket client.\n        \n        Args:\n            host: IP address or hostname of the SNP server\n            port: Port for REST API (default: 9089)\n            username: Authentication username\n            password: Authentication password\n        \"\"\"\n        self.host = host\n        self.port = port\n        self.username = username\n        self.password = password\n        self.api_base = f\"https://{host}:{port}/api/\"\n        self.ws_addr = f\"wss://{host}/smm\"\n        self.jwt_token = None\n        self.websocket = None\n        \n    def authenticate(self):\n        \"\"\"\n        Authenticate with the REST API to get JWT token.\n        \n        Returns:\n            str: JWT authentication token\n        \"\"\"\n        print(f\"[{datetime.now().strftime('%H:%M:%S')}] Authenticating with REST API...\")\n        \n        auth_url = f\"{self.api_base}auth\"\n        auth_data = {\n            \"username\": self.username,\n            \"password\": self.password\n        }\n        \n        try:\n            response = requests.post(\n                auth_url,\n                json=auth_data,\n                verify=False,  # Skip SSL verification for self-signed certs\n                timeout=10\n            )\n            response.raise_for_status()\n            \n            self.jwt_token = response.text.strip('\"')  # Remove quotes if present\n            print(f\"[{datetime.now().strftime('%H:%M:%S')}] Authentication successful!\")\n            return self.jwt_token\n            \n        except requests.exceptions.RequestException as e:\n            print(f\"[ERROR] Authentication failed: {e}\")\n            sys.exit(1)\n    \n    async def connect_and_retrieve_data(self, element_ip=None):\n        \"\"\"\n        Connect to WebSocket, authenticate, and retrieve data.\n        \n        Args:\n            element_ip: IP address of the element to query (defaults to host IP)\n        \"\"\"\n        if element_ip is None:\n            element_ip = self.host\n            \n        # Create SSL context that doesn't verify certificates\n        ssl_context = ssl.create_default_context()\n        ssl_context.check_hostname = False\n        ssl_context.verify_mode = ssl.CERT_NONE\n        \n        print(f\"[{datetime.now().strftime('%H:%M:%S')}] Connecting to WebSocket: {self.ws_addr}\")\n        \n        try:\n            async with websockets.connect(\n                self.ws_addr,\n                ssl=ssl_context,\n                ping_interval=30,\n                ping_timeout=10\n            ) as websocket:\n                self.websocket = websocket\n                print(f\"[{datetime.now().strftime('%H:%M:%S')}] WebSocket connected!\")\n                \n                # Send JWT token as first message\n                print(f\"[{datetime.now().strftime('%H:%M:%S')}] Sending authentication token...\")\n                await websocket.send(self.jwt_token)\n                \n                # Wait for authentication response or keepalive\n                auth_response = await websocket.recv()\n                print(f\"[{datetime.now().strftime('%H:%M:%S')}] Server response: {auth_response}\")\n                \n                # Request all objects data\n                request_msg = {\n                    \"msgType\": \"getAllObjects\",\n                    \"elementIp\": element_ip\n                }\n                \n                print(f\"[{datetime.now().strftime('%H:%M:%S')}] Requesting data: {json.dumps(request_msg)}\")\n                await websocket.send(json.dumps(request_msg))\n                \n                # Receive and process responses\n                print(f\"[{datetime.now().strftime('%H:%M:%S')}] Waiting for data...\")\n                messages_received = []\n                \n                # Set a timeout for receiving messages\n                timeout = 30  # seconds\n                start_time = asyncio.get_event_loop().time()\n                \n                while True:\n                    try:\n                        # Check for timeout\n                        if asyncio.get_event_loop().time() - start_time > timeout:\n                            print(f\"[{datetime.now().strftime('%H:%M:%S')}] Timeout reached, stopping...\")\n                            break\n                        \n                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)\n                        messages_received.append(message)\n                        \n                        # Try to parse as JSON for display\n                        try:\n                            msg_json = json.loads(message)\n                            msg_type = msg_json.get('msgType', 'unknown')\n                            print(f\"[{datetime.now().strftime('%H:%M:%S')}] Received message type: {msg_type}\")\n                            \n                            # If it's a keepalive, continue listening\n                            if msg_type == \"fmmStatus\" and msg_json.get('event') == 'keepalive':\n                                continue\n                            \n                            # If we got a substantial response, we might be done\n                            if msg_type != \"fmmStatus\":\n                                print(f\"[{datetime.now().strftime('%H:%M:%S')}] Received data message!\")\n                                # Wait a bit more in case there are additional messages\n                                await asyncio.sleep(2)\n                                \n                        except json.JSONDecodeError:\n                            print(f\"[{datetime.now().strftime('%H:%M:%S')}] Received non-JSON message\")\n                            \n                    except asyncio.TimeoutError:\n                        # No more messages after timeout\n                        print(f\"[{datetime.now().strftime('%H:%M:%S')}] No more messages, closing connection...\")\n                        break\n                \n                # Save the collected data\n                self.save_data(messages_received, element_ip)\n                \n        except Exception as e:\n            print(f\"[ERROR] WebSocket error: {e}\")\n            sys.exit(1)\n    \n    def save_data(self, messages, element_ip):\n        \"\"\"\n        Save received messages to a file in a readable format.\n        \n        Args:\n            messages: List of message strings received\n            element_ip: IP address queried\n        \"\"\"\n        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n        output_file = f\"snp_data_{element_ip.replace('.', '_')}_{timestamp}.json\"\n        \n        # Parse and format messages\n        formatted_data = {\n            \"query_time\": datetime.now().isoformat(),\n            \"element_ip\": element_ip,\n            \"messages_count\": len(messages),\n            \"messages\": []\n        }\n        \n        for idx, msg in enumerate(messages):\n            try:\n                # Try to parse as JSON for better formatting\n                msg_json = json.loads(msg)\n                formatted_data[\"messages\"].append({\n                    \"index\": idx,\n                    \"data\": msg_json\n                })\n            except json.JSONDecodeError:\n                # If not JSON, save as raw string\n                formatted_data[\"messages\"].append({\n                    \"index\": idx,\n                    \"raw\": msg\n                })\n        \n        # Save to file with pretty printing\n        with open(output_file, 'w') as f:\n            json.dump(formatted_data, f, indent=2, sort_keys=False)\n        \n        print(f\"\\n[{datetime.now().strftime('%H:%M:%S')}] Data saved to: {output_file}\")\n        print(f\"Total messages received: {len(messages)}\")\n        \n        # Also print a summary to console\n        print(\"\\n\" + \"=\"*60)\n        print(\"DATA SUMMARY\")\n        print(\"=\"*60)\n        for idx, msg in enumerate(formatted_data[\"messages\"]):\n            if \"data\" in msg:\n                msg_type = msg[\"data\"].get(\"msgType\", \"unknown\")\n                print(f\"\\nMessage {idx}: Type = {msg_type}\")\n                if msg_type != \"fmmStatus\":\n                    print(json.dumps(msg[\"data\"], indent=2))\n            else:\n                print(f\"\\nMessage {idx}: {msg.get('raw', '')[:100]}...\")\n        print(\"=\"*60)\n\n\ndef main():\n    \"\"\"Main entry point for the script.\"\"\"\n    print(\"=\"*60)\n    print(\"SNP WebSocket Client\")\n    print(\"=\"*60)\n    \n    # Configuration - UPDATE THESE VALUES\n    HOST = \"137.237.176.76\"  # SNP server IP/hostname\n    PORT = 9089               # REST API port\n    USERNAME = \"admin\"        # Authentication username\n    PASSWORD = \"password\"     # Authentication password\n    ELEMENT_IP = None         # Element IP to query (None = use HOST)\n    \n    print(f\"\\nConfiguration:\")\n    print(f\"  Host: {HOST}\")\n    print(f\"  Port: {PORT}\")\n    print(f\"  Username: {USERNAME}\")\n    print(f\"  Element IP: {ELEMENT_IP or HOST}\")\n    print()\n    \n    # Create client\n    client = SNPWebSocketClient(HOST, PORT, USERNAME, PASSWORD)\n    \n    # Authenticate\n    client.authenticate()\n    \n    # Connect and retrieve data\n    print()\n    asyncio.run(client.connect_and_retrieve_data(ELEMENT_IP))\n    \n    print(f\"\\n[{datetime.now().strftime('%H:%M:%S')}] Done!\")\n\n\nif __name__ == \"__main__\":\n    main()\n"
}
```

**Output:**
```
Wrote file successfully.
```

---

## Assistant (Build · claude-sonnet-4-5 · 4.1s)

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "id": "1",
      "content": "Create Python WebSocket client script for SNP connection",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Implement authentication flow (REST API + JWT)",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Implement WebSocket connection and message handling",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Add data retrieval via getAllObjects command",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "5",
      "content": "Save received data in readable format (JSON)",
      "status": "completed",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Create requirements.txt for dependencies",
      "status": "in_progress",
      "priority": "medium"
    }
  ]
}
```

**Output:**
```
[
  {
    "id": "1",
    "content": "Create Python WebSocket client script for SNP connection",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "2",
    "content": "Implement authentication flow (REST API + JWT)",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "3",
    "content": "Implement WebSocket connection and message handling",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "4",
    "content": "Add data retrieval via getAllObjects command",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "5",
    "content": "Save received data in readable format (JSON)",
    "status": "completed",
    "priority": "medium"
  },
  {
    "id": "6",
    "content": "Create requirements.txt for dependencies",
    "status": "in_progress",
    "priority": "medium"
  }
]
```

---

## Assistant (Build · claude-sonnet-4-5 · 2.7s)

**Tool: write**

**Input:**
```json
{
  "filePath": "/home/imagine/snp-exporter/requirements.txt",
  "content": "websockets>=12.0\nrequests>=2.31.0\nurllib3>=2.0.0\n"
}
```

**Error:**
```
Error: You must read file /home/imagine/snp-exporter/requirements.txt before overwriting it. Use the Read tool first
```

---

## Assistant (Build · claude-sonnet-4-5 · 1.9s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/imagine/snp-exporter/requirements.txt"
}
```

**Output:**
```
<file>
00001| pyyaml
00002| asyncio
00003| fastapi
00004| aiohttp
00005| prometheus_client
00006| uvicorn
00007| websockets
00008| aiosqlite
00009| jinja2

(End of file - total 9 lines)
</file>
```

---

## Assistant (Build · claude-sonnet-4-5 · 3.3s)

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/imagine/snp-exporter/requirements.txt",
  "oldString": "pyyaml\nasyncio\nfastapi\naiohttp\nprometheus_client\nuvicorn\nwebsockets\naiosqlite\njinja2",
  "newString": "pyyaml\nasyncio\nfastapi\naiohttp\nprometheus_client\nuvicorn\nwebsockets>=12.0\naiosqlite\njinja2\nrequests>=2.31.0\nurllib3>=2.0.0"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · claude-sonnet-4-5 · 3.3s)

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "id": "1",
      "content": "Create Python WebSocket client script for SNP connection",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "2",
      "content": "Implement authentication flow (REST API + JWT)",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "3",
      "content": "Implement WebSocket connection and message handling",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "4",
      "content": "Add data retrieval via getAllObjects command",
      "status": "completed",
      "priority": "high"
    },
    {
      "id": "5",
      "content": "Save received data in readable format (JSON)",
      "status": "completed",
      "priority": "medium"
    },
    {
      "id": "6",
      "content": "Create requirements.txt for dependencies",
      "status": "completed",
      "priority": "medium"
    }
  ]
}
```

**Output:**
```
[
  {
    "id": "1",
    "content": "Create Python WebSocket client script for SNP connection",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "2",
    "content": "Implement authentication flow (REST API + JWT)",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "3",
    "content": "Implement WebSocket connection and message handling",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "4",
    "content": "Add data retrieval via getAllObjects command",
    "status": "completed",
    "priority": "high"
  },
  {
    "id": "5",
    "content": "Save received data in readable format (JSON)",
    "status": "completed",
    "priority": "medium"
  },
  {
    "id": "6",
    "content": "Create requirements.txt for dependencies",
    "status": "completed",
    "priority": "medium"
  }
]
```

---

## Assistant (Build · claude-sonnet-4-5 · 9.7s)

Perfect! I've created a Python WebSocket client for your SNP connection. Here's what I built:

## Created Files

**snp_websocket_client.py** - Main script with the following features:

### Key Features:
1. **REST API Authentication** - Gets JWT token from the `/api/auth` endpoint
2. **Secure WebSocket Connection** - Connects via WSS with SSL support
3. **JWT Authentication** - Sends token as first message after connection
4. **Data Retrieval** - Sends `getAllObjects` command to retrieve data
5. **Message Handling** - Processes keepalive and data messages
6. **Pretty JSON Output** - Saves data in a timestamped, readable JSON file

### How to Use:

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure the script** (edit these variables at the bottom of `snp_websocket_client.py`):
```python
HOST = "137.237.176.76"  # Your SNP server IP
PORT = 9089              # REST API port
USERNAME = "admin"       # Your username
PASSWORD = "password"    # Your password
ELEMENT_IP = None        # Element IP to query (None = use HOST)
```

3. **Run the script:**
```bash
python3 snp_websocket_client.py
```

### Output Format:

The script saves data to a file named: `snp_data_<ip>_<timestamp>.json`

Example output structure:
```json
{
  "query_time": "2026-02-07T12:30:45.123456",
  "element_ip": "137.237.176.76",
  "messages_count": 3,
  "messages": [
    {
      "index": 0,
      "data": {
        "msgType": "fmmStatus",
        "event": "keepalive",
        "status": "success"
      }
    },
    {
      "index": 1,
      "data": {
        "msgType": "getAllObjects",
        "objects": [...]
      }
    }
  ]
}
```

The script also prints a summary to the console showing message types and key data received.

---

