import sqlite3
import os
from datetime import datetime

DB_FILE = "sentinel.db"

# ─── Initialize Database ──────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            port INTEGER DEFAULT 80,
            location TEXT DEFAULT 'Unknown',
            added_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_ip TEXT NOT NULL,
            camera_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uptime_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_ip TEXT NOT NULL,
            camera_name TEXT NOT NULL,
            status TEXT NOT NULL,
            uptime_pct REAL DEFAULT 0,
            total_checks INTEGER DEFAULT 0,
            recorded_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            hostname TEXT,
            device_type TEXT,
            open_ports TEXT,
            scanned_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] Database initialized: " + DB_FILE)

# ─── Camera Operations ────────────────────────────────────

def save_camera(ip, name, port=80, location="Unknown"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO cameras 
            (ip, name, port, location, added_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip, name, port, location, str(datetime.now())))
        conn.commit()
    except Exception as e:
        print("[DB] Error saving camera: " + str(e))
    finally:
        conn.close()

def load_cameras():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT ip, name, port, location FROM cameras")
    rows = cursor.fetchall()
    conn.close()
    cameras = []
    for row in rows:
        cameras.append({
            "ip": row[0],
            "name": row[1],
            "port": row[2],
            "location": row[3],
            "hostname": row[1],
            "open_ports": [row[2]]
        })
    return cameras

def delete_camera(ip):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cameras WHERE ip = ?", (ip,))
    conn.commit()
    conn.close()

# ─── Event Operations ─────────────────────────────────────

def log_event(camera_ip, camera_name, event_type):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (camera_ip, camera_name, event_type, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (camera_ip, camera_name, event_type, str(datetime.now())))
    conn.commit()
    conn.close()

def get_recent_events(limit=50):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT camera_name, camera_ip, event_type, timestamp
        FROM events
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ─── Uptime Operations ────────────────────────────────────

def save_uptime(camera_ip, camera_name, status, uptime_pct, total_checks):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO uptime_records
        (camera_ip, camera_name, status, uptime_pct, total_checks, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (camera_ip, camera_name, status, uptime_pct,
          total_checks, str(datetime.now())))
    conn.commit()
    conn.close()

def get_uptime_history(camera_ip, limit=100):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT status, uptime_pct, total_checks, recorded_at
        FROM uptime_records
        WHERE camera_ip = ?
        ORDER BY recorded_at DESC
        LIMIT ?
    ''', (camera_ip, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ─── Scan Operations ──────────────────────────────────────

def save_scan_result(ip, hostname, device_type, open_ports):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scan_results
        (ip, hostname, device_type, open_ports, scanned_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (ip, hostname, device_type,
          str(open_ports), str(datetime.now())))
    conn.commit()
    conn.close()

def get_scan_history(limit=100):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ip, hostname, device_type, open_ports, scanned_at
        FROM scan_results
        ORDER BY scanned_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ─── Test ─────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    save_camera("192.168.1.1", "Router", 80, "Main Office")
    save_camera("192.168.1.100", "Camera1", 554, "Front Door")
    log_event("192.168.1.100", "Camera1", "went_offline")
    log_event("192.168.1.100", "Camera1", "came_online")
    print("\nCameras in database:")
    for cam in load_cameras():
        print(" -", cam["name"], cam["ip"])
    print("\nRecent events:")
    for event in get_recent_events():
        print(" -", event)
    print("\n[DB] All tests passed.")