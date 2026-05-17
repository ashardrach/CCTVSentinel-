# CCTV Sentinel 🎥

A professional CCTV network monitoring and management system
built in Python. For authorized use on networks you own only.

## Features

### Phase 1 — Network Discovery
- Automatic subnet detection
- Multi-threaded network scanning (50 threads)
- CCTV device detection (IP cameras, NVR, DVR)
- Port identification (RTSP, HTTP, Hikvision, Dahua)
- RTSP stream URL generation
- Save scan results to JSON and CSV

### Phase 2 — Uptime Monitoring
- Monitor cameras every 30 seconds
- Detect online/offline status changes
- Desktop popup notifications
- Uptime percentage tracking
- Event log with timestamps
- Automatic report generation

### Phase 3 — GUI Dashboard
- Professional dark theme desktop application
- Network scan button
- Add/Remove cameras manually
- Live color-coded status table
- Real-time event log
- Save report button

### Phase 4 — Professional Features
- SQLite database (permanent storage)
- Camera location tracking
- Full event history and audit trail
- Email alerts via Gmail SMTP
- Telegram bot instant alerts
- Scheduled automatic scanning
- SHA256 hashed login system
- Unified main menu

## Files
- main.py      — entry point with login and main menu
- sentinel.py  — network discovery scanner
- monitor.py   — terminal uptime monitor
- gui.py       — GUI dashboard
- database.py  — SQLite database operations
- alerts.py    — email and Telegram alerts
- scheduler.py — scheduled scanning
- auth.py      — login authentication system

## Requirements
pip install python-nmap colorama requests plyer schedule python-telegram-bot

Also install Nmap from nmap.org

## How to Run
python main.py

## Legal Warning
This tool is for authorized use only. Only scan networks
and systems you own or have explicit written permission
to monitor. Unauthorized scanning is illegal.

## Real World Use Cases
- CCTV network audits for small businesses
- Camera uptime monitoring services
- Network inventory for security installers
- Automated health reporting for clients

## Built By
ashardrach — cybersecurity student building
professional network security tools.
GitHub: github.com/ashardrach