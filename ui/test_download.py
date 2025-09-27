#!/usr/bin/env python3
"""
Simple test server for download functionality
"""

import http.server
import socketserver
import os
import json
from datetime import datetime

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/download/'):
            self.handle_download()
        else:
            super().do_GET()
    
    def handle_download(self):
        """Handle file downloads"""
        try:
            # Parse the path: /api/download/logs/filename or /api/download/exports/filename
            path_parts = self.path.split('/')
            if len(path_parts) >= 4:
                file_type = path_parts[3]  # logs or exports
                filename = '/'.join(path_parts[4:])  # filename (in case it has path separators)
            else:
                self.send_error(400, "Invalid download path")
                return
            
            # Get the file path
            user_home = os.path.expanduser('~')
            file_dir = os.path.join(user_home, 'Documents', 'chaos-guardian', file_type)
            file_path = os.path.join(file_dir, filename)
            
            print(f"Download request: {file_type}/{filename}")
            print(f"Looking for file at: {file_path}")
            print(f"File exists: {os.path.exists(file_path)}")
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                self.send_error(404, f"File not found: {filename}")
                return
            
            # Serve the file
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
                
            print(f"File served successfully: {filename}")
            
        except Exception as e:
            print(f"Download error: {e}")
            self.send_error(500, f"Download failed: {str(e)}")

def start_test_server(port=8081):
    """Start the test server"""
    with socketserver.TCPServer(("", port), TestHandler) as httpd:
        print(f"🧪 Test Download Server running at http://localhost:{port}")
        print(f"📥 Test downloads at http://localhost:{port}/api/download/logs/filename")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    start_test_server()
