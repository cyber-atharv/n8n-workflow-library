#!/usr/bin/env python3
"""
scripts/serve.py
Local lightweight HTTP server for Atharv Studio n8n Workflow Library.
Serves web interface and workflow catalog with CORS support.
"""

import os
import sys
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class AtharvStudioHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        return super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

def find_free_port(start_port=8080):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port

def start_server(port=None):
    if port is None:
        port = find_free_port(8080)

    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, AtharvStudioHTTPHandler)
    url = f"http://localhost:{port}/web/"
    
    print("=" * 65)
    print("  [*] Atharv Studio: n8n Workflow Library Running Locally")
    print(f"  [*] Web Application: {url}")
    print(f"  [*] Project Root:     {BASE_DIR}")
    print(f"  [*] Press Ctrl+C to stop the server")
    print("=" * 65)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Server stopped.")

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else None
    start_server(p)
