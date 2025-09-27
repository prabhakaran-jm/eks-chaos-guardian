# EKS Chaos Guardian - Web UI

This directory contains the web-based dashboard for the EKS Chaos Guardian AI agent.

## Files

- **`index.html`** - Main dashboard interface with chaos scenarios and controls
- **`server.py`** - Python HTTP server that serves the UI and handles API requests
- **`.gitignore`** - Excludes temporary files and cache from version control

## Features

- **System Status Dashboard** - Real-time monitoring of EKS cluster, Bedrock agent, and Lambda functions
- **Chaos Scenarios** - Interactive buttons to trigger various failure scenarios
- **File Downloads** - Generate and download log files and CSV exports
- **OS-Agnostic** - Works on Windows, macOS, and Linux
- **Responsive Design** - Modern UI with styled modals and notifications

## Usage

1. **Start the server:**
   ```bash
   cd ui
   python server.py
   ```

2. **Open the dashboard:**
   - Navigate to `http://localhost:8080`
   - The dashboard will load with system status and available scenarios

3. **Generate files:**
   - Click "View Logs" to create and download system log files
   - Click "Export Results" to create and download CSV reports

## File Storage

Generated files are stored in OS-appropriate locations:
- **Windows:** `Documents/chaos-guardian/`
- **macOS:** `Documents/chaos-guardian/`
- **Linux:** `chaos-guardian/`

## API Endpoints

- `GET /` - Serves the main dashboard
- `GET /api/status` - Returns system status
- `POST /api/logs` - Creates and returns download URL for log files
- `POST /api/export` - Creates and returns download URL for CSV exports
- `GET /api/download/logs/{filename}` - Downloads log files
- `GET /api/download/exports/{filename}` - Downloads CSV files

## Requirements

- Python 3.6+
- Modern web browser
- No additional dependencies required
