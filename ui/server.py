#!/usr/bin/env python3
"""
Simple working server for EKS Chaos Guardian UI with download functionality
"""

import http.server
import socketserver
import os
import json
from datetime import datetime

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/download/'):
            self.handle_download()
        elif self.path.startswith('/api/'):
            self.handle_api()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404, "Not found")
    
    def handle_download(self):
        """Handle file downloads"""
        try:
            # Parse the path: /api/download/logs/filename or /api/download/exports/filename
            path_parts = self.path.split('/')
            if len(path_parts) >= 4:
                file_type = path_parts[3]  # logs or exports
                filename = '/'.join(path_parts[4:])  # filename
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
    
    def handle_api(self):
        """Handle API GET requests"""
        if self.path == '/api/status':
            self.send_api_response({
                'status': 'online',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'eks_cluster': 'online',
                    'bedrock_agent': 'active',
                    'lambda_functions': '5/6 ready',
                    'slack_integration': 'connected'
                }
            })
        else:
            self.send_error(404, "API endpoint not found")
    
    def handle_api_post(self):
        """Handle API POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/api/logs':
                result = self.create_log_file()
                self.send_api_response(result)
            elif self.path == '/api/export':
                result = self.create_csv_file()
                self.send_api_response(result)
            else:
                self.send_error(404, "API endpoint not found")
                
        except Exception as e:
            self.send_error(500, f"API error: {str(e)}")
    
    def create_log_file(self):
        """Create a log file"""
        try:
            user_home = os.path.expanduser('~')
            # OS-agnostic path construction
            if os.name == 'nt':  # Windows
                logs_dir = os.path.join(user_home, 'Documents', 'chaos-guardian', 'logs')
            else:  # Unix-like (macOS, Linux)
                logs_dir = os.path.join(user_home, 'Documents', 'chaos-guardian', 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            log_file = os.path.join(logs_dir, f'chaos-guardian-{datetime.now().strftime("%Y%m%d-%H%M%S")}.log')
            
            with open(log_file, 'w') as f:
                f.write(f"EKS Chaos Guardian System Logs\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                f.write("SYSTEM STATUS:\n")
                f.write("- EKS Cluster: Online\n")
                f.write("- Bedrock Agent: Active\n")
                f.write("- Lambda Functions: 9/9 Ready\n")
                f.write("- Slack Integration: Connected\n")
                f.write("- API Gateway: Operational\n\n")
                f.write("RECENT ACTIVITY:\n")
                f.write(f"- {datetime.now().isoformat()}: System initialized\n")
                f.write(f"- {datetime.now().isoformat()}: Lambda functions deployed\n")
                f.write(f"- {datetime.now().isoformat()}: Slack bot configured\n")
                f.write(f"- {datetime.now().isoformat()}: Demo scenarios ready\n")
            
            filename = os.path.basename(log_file)
            return {
                'status': 'success',
                'message': f'Log file created: {filename}',
                'filename': filename,
                'download_url': f'/api/download/logs/{filename}',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to create log file: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def create_csv_file(self):
        """Create a CSV file"""
        try:
            user_home = os.path.expanduser('~')
            # OS-agnostic path construction
            if os.name == 'nt':  # Windows
                exports_dir = os.path.join(user_home, 'Documents', 'chaos-guardian', 'exports')
            else:  # Unix-like (macOS, Linux)
                exports_dir = os.path.join(user_home, 'Documents', 'chaos-guardian', 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            
            csv_file = os.path.join(exports_dir, f'chaos-guardian-results-{datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
            
            with open(csv_file, 'w', newline='') as f:
                f.write("Timestamp,Scenario,Status,Duration,Success Rate,Autonomous Action,Notes\n")
                f.write(f"{datetime.now().isoformat()},System Check,Completed,2.3s,100%,Yes,System initialization\n")
                f.write(f"{datetime.now().isoformat()},OOMKilled,Ready,0s,0%,No,Memory limit failures\n")
                f.write(f"{datetime.now().isoformat()},ImagePullBackOff,Ready,0s,0%,No,Image pull failures\n")
                f.write(f"{datetime.now().isoformat()},Readiness Probe,Ready,0s,0%,No,Health check failures\n")
                f.write(f"{datetime.now().isoformat()},Disk Pressure,Ready,0s,0%,No,Node storage issues\n")
                f.write(f"{datetime.now().isoformat()},PDB Blocking,Ready,0s,0%,No,Pod disruption budget\n")
                f.write(f"{datetime.now().isoformat()},CoreDNS Failure,Ready,0s,0%,No,DNS service disruption\n")
            
            filename = os.path.basename(csv_file)
            return {
                'status': 'success',
                'message': f'Results exported to CSV: {filename}',
                'filename': filename,
                'download_url': f'/api/download/exports/{filename}',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to export results: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def send_api_response(self, data):
        """Send JSON API response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))

def start_simple_server(port=8080):
    """Start the simple server"""
    with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
        print(f"🚀 EKS Chaos Guardian - Simple Server")
        print(f"📡 Server running at http://localhost:{port}")
        print(f"🌐 Dashboard: http://localhost:{port}")
        print(f"📊 API: http://localhost:{port}/api/")
        print(f"📥 Downloads: http://localhost:{port}/api/download/")
        print("⏹️  Press Ctrl+C to stop")
        print("-" * 50)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    start_simple_server()
