#!/usr/bin/env python3
"""
EKS Chaos Guardian - Web UI Server
Simple HTTP server for the demo dashboard
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any
import threading
import subprocess

class ChaosGuardianHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the Chaos Guardian UI"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/api/status':
            self.send_api_response(self.get_system_status())
            return
        elif self.path == '/api/scenarios':
            self.send_api_response(self.get_scenarios())
            return
        elif self.path.startswith('/api/scenario/'):
            scenario_id = self.path.split('/')[-1]
            self.send_api_response(self.get_scenario_status(scenario_id))
            return
        
        super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith('/api/scenario/'):
            scenario_id = self.path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                action = data.get('action', 'run')
                
                if action == 'run':
                    result = self.run_scenario(scenario_id)
                    self.send_api_response(result)
                elif action == 'stop':
                    result = self.stop_scenario(scenario_id)
                    self.send_api_response(result)
                else:
                    self.send_api_response({'error': 'Unknown action'}, 400)
                    
            except json.JSONDecodeError:
                self.send_api_response({'error': 'Invalid JSON'}, 400)
        else:
            self.send_api_response({'error': 'Not found'}, 404)
    
    def send_api_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON API response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'status': 'online',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'eks_cluster': 'online',
                'bedrock_agent': 'active',
                'lambda_functions': '5/6 ready',
                'slack_integration': 'connected'
            },
            'metrics': {
                'detection_time': '45s',
                'success_rate': '92%',
                'recovery_time': '3.2m',
                'autonomous_actions': '68%'
            }
        }
    
    def get_scenarios(self) -> Dict[str, Any]:
        """Get available scenarios"""
        return {
            'scenarios': {
                'oomkilled': {
                    'name': 'OOMKilled',
                    'description': 'Memory limit failures',
                    'status': 'ready',
                    'estimated_time': '2-3 minutes',
                    'risk_level': 'LOW'
                },
                'image-pull-backoff': {
                    'name': 'ImagePullBackOff',
                    'description': 'Image pull failures',
                    'status': 'ready',
                    'estimated_time': '1-2 minutes',
                    'risk_level': 'MEDIUM'
                },
                'readiness-probe': {
                    'name': 'Readiness Probe',
                    'description': 'Health check failures',
                    'status': 'ready',
                    'estimated_time': '1-2 minutes',
                    'risk_level': 'LOW'
                },
                'disk-pressure': {
                    'name': 'Disk Pressure',
                    'description': 'Node storage issues',
                    'status': 'ready',
                    'estimated_time': '3-5 minutes',
                    'risk_level': 'HIGH'
                },
                'pdb-blocking': {
                    'name': 'PDB Blocking',
                    'description': 'Pod disruption budget',
                    'status': 'ready',
                    'estimated_time': '2-4 minutes',
                    'risk_level': 'HIGH'
                },
                'coredns-failure': {
                    'name': 'CoreDNS Failure',
                    'description': 'DNS service disruption',
                    'status': 'ready',
                    'estimated_time': '1-2 minutes',
                    'risk_level': 'LOW'
                }
            }
        }
    
    def get_scenario_status(self, scenario_id: str) -> Dict[str, Any]:
        """Get specific scenario status"""
        scenarios = self.get_scenarios()['scenarios']
        
        if scenario_id not in scenarios:
            return {'error': 'Scenario not found'}
        
        return {
            'scenario_id': scenario_id,
            'scenario': scenarios[scenario_id],
            'status': scenarios[scenario_id]['status'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def run_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Run a chaos scenario"""
        print(f"Running scenario: {scenario_id}")
        
        # In a real implementation, this would call the actual scenario script
        # For demo purposes, we'll simulate the execution
        
        try:
            # Simulate running the scenario
            if scenario_id == 'oomkilled':
                cmd = ['python', '../demo/scenarios/oomkilled.py']
            elif scenario_id == 'image-pull-backoff':
                cmd = ['python', '../demo/scenarios/image_pull_backoff.py']
            elif scenario_id == 'readiness-probe':
                cmd = ['python', '../demo/scenarios/readiness_probe.py']
            else:
                # For other scenarios, just simulate
                cmd = ['echo', f'Simulating {scenario_id} scenario']
            
            # Run in background thread
            def run_cmd():
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    print(f"Scenario {scenario_id} completed: {result.returncode}")
                except subprocess.TimeoutExpired:
                    print(f"Scenario {scenario_id} timed out")
                except Exception as e:
                    print(f"Scenario {scenario_id} failed: {e}")
            
            thread = threading.Thread(target=run_cmd)
            thread.daemon = True
            thread.start()
            
            return {
                'scenario_id': scenario_id,
                'status': 'running',
                'message': f'Scenario {scenario_id} started',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'scenario_id': scenario_id,
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def stop_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Stop a running scenario"""
        print(f"Stopping scenario: {scenario_id}")
        
        return {
            'scenario_id': scenario_id,
            'status': 'stopped',
            'message': f'Scenario {scenario_id} stopped',
            'timestamp': datetime.utcnow().isoformat()
        }

def start_server(port: int = 8080):
    """Start the web server"""
    try:
        with socketserver.TCPServer(("", port), ChaosGuardianHandler) as httpd:
            print(f"🚀 EKS Chaos Guardian UI Server")
            print(f"📡 Server running at http://localhost:{port}")
            print(f"🌐 Dashboard: http://localhost:{port}")
            print(f"📊 API: http://localhost:{port}/api/")
            print(f"⏹️  Press Ctrl+C to stop")
            print("-" * 50)
            
            # Open browser automatically
            webbrowser.open(f'http://localhost:{port}')
            
            # Start server
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use")
            print(f"💡 Try a different port: python server.py {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    port = 8080
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number")
            sys.exit(1)
    
    print("🤖 EKS Chaos Guardian - Web UI Server")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('index.html'):
        print("❌ index.html not found. Please run from the ui/ directory")
        sys.exit(1)
    
    start_server(port)

if __name__ == "__main__":
    main()
