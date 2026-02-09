#!/usr/bin/env python3
"""
SNP WebSocket Client
Connects to SNP via secure WebSocket, authenticates, and retrieves data.
"""

import asyncio
import websockets
import json
import requests
import ssl
import sys
from datetime import datetime
from pathlib import Path
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SNPWebSocketClient:
    """Client for connecting to SNP via WebSocket and retrieving data."""
    
    def __init__(self, host, port=9089, username="admin", password="password"):
        """
        Initialize the SNP WebSocket client.
        
        Args:
            host: IP address or hostname of the SNP server
            port: Port for REST API (default: 9089)
            username: Authentication username
            password: Authentication password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.api_base = f"https://{host}:{port}/api/"
        self.ws_addr = f"wss://{host}/smm"
        self.jwt_token = None
        self.websocket = None
        
    def authenticate(self):
        """
        Authenticate with the REST API to get JWT token.
        
        Returns:
            str: JWT authentication token
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Authenticating with REST API...")
        
        auth_url = f"{self.api_base}auth"
        auth_data = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = requests.post(
                auth_url,
                json=auth_data,
                verify=False,  # Skip SSL verification for self-signed certs
                timeout=10
            )
            response.raise_for_status()
            
            self.jwt_token = response.text.strip('"')  # Remove quotes if present
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Authentication successful!")
            return self.jwt_token
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Authentication failed: {e}")
            sys.exit(1)
    
    async def connect_and_retrieve_data(self, element_ip=None):
        """
        Connect to WebSocket, authenticate, and retrieve data.
        
        Args:
            element_ip: IP address of the element to query (defaults to host IP)
        """
        if element_ip is None:
            element_ip = self.host
            
        # Create SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to WebSocket: {self.ws_addr}")
        
        try:
            async with websockets.connect(
                self.ws_addr,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10,
                max_size=50 * 1024 * 1024  # 50MB max message size
            ) as websocket:
                self.websocket = websocket
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WebSocket connected!")
                
                # Send JWT token as first message
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending authentication token...")
                await websocket.send(self.jwt_token)
                
                # Wait for authentication response or keepalive
                auth_response = await websocket.recv()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Server response: {auth_response}")
                
                # Request all objects data
                request_msg = {
                    "msgType": "getAllObjects",
                    "elementIp": element_ip
                }
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Requesting data: {json.dumps(request_msg)}")
                await websocket.send(json.dumps(request_msg))
                
                # Receive and process responses
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for data...")
                messages_received = []
                
                # Set a timeout for receiving messages
                timeout = 30  # seconds
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    try:
                        # Check for timeout
                        if asyncio.get_event_loop().time() - start_time > timeout:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout reached, stopping...")
                            break
                        
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        messages_received.append(message)
                        
                        # Try to parse as JSON for display
                        try:
                            msg_json = json.loads(message)
                            msg_type = msg_json.get('msgType', 'unknown')
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received message type: {msg_type}")
                            
                            # If it's a keepalive, continue listening
                            if msg_type == "fmmStatus" and msg_json.get('event') == 'keepalive':
                                continue
                            
                            # If we got a substantial response, we might be done
                            if msg_type != "fmmStatus":
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Received data message!")
                                # Wait a bit more in case there are additional messages
                                await asyncio.sleep(2)
                                
                        except json.JSONDecodeError:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received non-JSON message")
                            
                    except asyncio.TimeoutError:
                        # No more messages after timeout
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No more messages, closing connection...")
                        break
                
                # Save the collected data
                self.save_data(messages_received, element_ip)
                
        except Exception as e:
            print(f"[ERROR] WebSocket error: {e}")
            sys.exit(1)
    
    def save_data(self, messages, element_ip):
        """
        Save received messages to a file in a readable format.
        
        Args:
            messages: List of message strings received
            element_ip: IP address queried
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"snp_data_{element_ip.replace('.', '_')}_{timestamp}.json"
        
        # Parse and format messages
        formatted_data = {
            "query_time": datetime.now().isoformat(),
            "element_ip": element_ip,
            "messages_count": len(messages),
            "messages": []
        }
        
        for idx, msg in enumerate(messages):
            try:
                # Try to parse as JSON for better formatting
                msg_json = json.loads(msg)
                formatted_data["messages"].append({
                    "index": idx,
                    "data": msg_json
                })
            except json.JSONDecodeError:
                # If not JSON, save as raw string
                formatted_data["messages"].append({
                    "index": idx,
                    "raw": msg
                })
        
        # Save to file with pretty printing
        with open(output_file, 'w') as f:
            json.dump(formatted_data, f, indent=2, sort_keys=False)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Data saved to: {output_file}")
        print(f"Total messages received: {len(messages)}")
        
        # Also print a summary to console
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        for idx, msg in enumerate(formatted_data["messages"]):
            if "data" in msg:
                msg_type = msg["data"].get("msgType", "unknown")
                print(f"\nMessage {idx}: Type = {msg_type}")
                if msg_type != "fmmStatus":
                    print(json.dumps(msg["data"], indent=2))
            else:
                print(f"\nMessage {idx}: {msg.get('raw', '')[:100]}...")
        print("="*60)


def main():
    """Main entry point for the script."""
    print("="*60)
    print("SNP WebSocket Client")
    print("="*60)
    
    # Prompt for SNP IP address
    print()
    HOST = input("Enter SNP IP address: ").strip()
    
    if not HOST:
        print("[ERROR] IP address is required!")
        sys.exit(1)
    
    # Fixed configuration
    PORT = 9089               # REST API port
    USERNAME = "admin"        # Authentication username
    PASSWORD = "password"     # Authentication password
    ELEMENT_IP = None         # Element IP to query (None = use HOST)
    
    print(f"\nConfiguration:")
    print(f"  Host: {HOST}")
    print(f"  Port: {PORT}")
    print(f"  Username: {USERNAME}")
    print(f"  Element IP: {ELEMENT_IP or HOST}")
    print()
    
    # Create client
    client = SNPWebSocketClient(HOST, PORT, USERNAME, PASSWORD)
    
    # Authenticate
    client.authenticate()
    
    # Connect and retrieve data
    print()
    asyncio.run(client.connect_and_retrieve_data(ELEMENT_IP))
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Done!")


if __name__ == "__main__":
    main()
