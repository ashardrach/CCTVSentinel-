# CCTV Sentinel 🎥

A professional network camera discovery and monitoring tool 
built in Python. For authorized use only.

## Features — Phase 1
- Automatic network subnet detection
- Multi-threaded scanning (50 simultaneous threads)
- CCTV port detection (RTSP, HTTP, Hikvision, Dahua)
- Device type identification
- Hostname resolution
- RTSP stream URL generation
- Web interface URL detection
- Save results to JSON and CSV
- Color-coded terminal output

## Detected Device Types
- IP Cameras
- NVR (Network Video Recorder)
- DVR (Digital Video Recorder)
- Hikvision devices
- Dahua devices
- General network devices

## CCTV Ports Scanned
- Port 554  — RTSP video streaming
- Port 80   — HTTP web interface
- Port 443  — HTTPS web interface
- Port 8080 — Alternative HTTP
- Port 9000 — Hikvision SDK
- Port 37777 — Dahua proprietary
- Port 34567 — DVR systems

## Legal Warning
This tool is for authorized use only. Only scan networks
and systems you own or have explicit written permission
to scan. Unauthorized scanning is illegal.

## How to Run
1. Install requirements:
   pip install python-nmap colorama requests
2. Install Nmap from nmap.org
3. Run:
   python sentinel.py

## Coming Soon
- Phase 2: Camera uptime monitoring
- Phase 3: GUI dashboard
- Phase 4: Alerts and scheduling

## Built By
ashardrach — cybersecurity student building 
professional network tools.