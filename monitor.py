import socket
import time
import json
import csv
import os
import threading
from datetime import datetime
from colorama import Fore, Style, init
from plyer import notification

init(autoreset=True)

# ─── Global State ─────────────────────────────────────────

camera_status = {}
status_lock = threading.Lock()
uptime_log = []
log_lock = threading.Lock()

# ─── Banner ───────────────────────────────────────────────

def print_banner():
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "   CCTV SENTINEL — Uptime Monitor")
    print(Fore.CYAN + "   Phase 2 — Real-time Camera Monitoring")
    print(Fore.CYAN + "=" * 60)

# ─── Ping Camera ──────────────────────────────────────────

def ping_camera(ip, port=80, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_camera(ip, port=80):
    ports_to_try = [port, 80, 554, 8080]
    for p in ports_to_try:
        if ping_camera(ip, p):
            return True, p
    return False, None

# ─── Alert ────────────────────────────────────────────────

def send_alert(camera_name, ip, status):
    title = "CCTV SENTINEL ALERT"
    if status == "offline":
        message = "Camera OFFLINE: " + camera_name + " (" + ip + ")"
    else:
        message = "Camera ONLINE: " + camera_name + " (" + ip + ")"
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="CCTV Sentinel",
            timeout=10
        )
    except:
        pass

# ─── Monitor Single Camera ────────────────────────────────

def monitor_camera(camera):
    ip = camera["ip"]
    name = camera.get("name", ip)
    check_port = int(camera.get("port", 80))

    with status_lock:
        camera_status[ip] = {
            "name": name,
            "ip": ip,
            "port": check_port,
            "status": "unknown",
            "last_seen": "Never",
            "uptime_count": 0,
            "downtime_count": 0,
            "total_checks": 0
        }

    while True:
        online, active_port = check_camera(ip, check_port)

        with status_lock:
            prev_status = camera_status[ip]["status"]
            camera_status[ip]["total_checks"] += 1

            if online:
                camera_status[ip]["status"] = "online"
                camera_status[ip]["last_seen"] = datetime.now().strftime("%H:%M:%S")
                camera_status[ip]["uptime_count"] += 1
                if prev_status == "offline":
                    send_alert(name, ip, "online")
                    uptime_log.append({
                        "timestamp": str(datetime.now()),
                        "camera": name,
                        "ip": ip,
                        "status": "came_online"
                    })
            else:
                camera_status[ip]["status"] = "offline"
                camera_status[ip]["downtime_count"] += 1
                if prev_status in ["online", "unknown"]:
                    send_alert(name, ip, "offline")
                    uptime_log.append({
                        "timestamp": str(datetime.now()),
                        "camera": name,
                        "ip": ip,
                        "status": "went_offline"
                    })

        time.sleep(30)

# ─── Dashboard ────────────────────────────────────────────

def calculate_uptime(cam):
    total = cam["total_checks"]
    if total == 0:
        return "N/A"
    pct = (cam["uptime_count"] / total) * 100
    return str(round(pct, 1)) + "%"

def print_dashboard():
    while True:
        time.sleep(10)

        with status_lock:
            cams = list(camera_status.values())

        if not cams:
            continue

        try:
            os.system("cls" if os.name == "nt" else "clear")
            print_banner()
            print(Fore.YELLOW + "\nLast updated: " +
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(Fore.WHITE + "=" * 60)
            print(Fore.WHITE + "{:<20} {:<16} {:<12} {:<8}".format(
                "Camera", "IP", "Status", "Uptime"))
            print(Fore.WHITE + "-" * 60)

            online_count = 0
            offline_count = 0

            for cam in cams:
                if cam["status"] == "online":
                    status_str = Fore.GREEN + "🟢 ONLINE   " + Style.RESET_ALL
                    online_count += 1
                elif cam["status"] == "offline":
                    status_str = Fore.RED + "🔴 OFFLINE  " + Style.RESET_ALL
                    offline_count += 1
                else:
                    status_str = Fore.YELLOW + "⏳ CHECKING " + Style.RESET_ALL

                uptime = calculate_uptime(cam)
                print("{:<20} {:<16} {} {:<8}".format(
                    cam["name"][:18],
                    cam["ip"],
                    status_str,
                    uptime
                ))

            print(Fore.WHITE + "=" * 60)
            print(Fore.GREEN + "Online:  " + str(online_count) +
                  Fore.RED + "   Offline: " + str(offline_count))
            print(Fore.WHITE + "\nPress Ctrl+C to stop and save report.")
        except Exception as e:
            pass

# ─── Save Report ──────────────────────────────────────────

def save_report():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "monitor_report_" + timestamp

    with open(filename + ".json", "w") as f:
        json.dump({
            "camera_status": list(camera_status.values()),
            "events": uptime_log
        }, f, indent=2)
    print(Fore.GREEN + "\n[+] Report saved: " + filename + ".json")

    if uptime_log:
        with open(filename + "_events.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=uptime_log[0].keys())
            writer.writeheader()
            writer.writerows(uptime_log)
        print(Fore.GREEN + "[+] Events saved: " + filename + "_events.csv")

# ─── Load Cameras ─────────────────────────────────────────

def load_cameras_from_scan():
    scan_files = [f for f in os.listdir(".")
                  if f.startswith("cctv_scan") and f.endswith(".json")]
    if not scan_files:
        return []
    latest = sorted(scan_files)[-1]
    print(Fore.GREEN + "[+] Loading from: " + latest)
    with open(latest, "r") as f:
        devices = json.load(f)
    cameras = []
    for d in devices:
        port = 80
        if d.get("open_ports"):
            port = d["open_ports"][0]
        cameras.append({
            "ip": d["ip"],
            "name": d.get("hostname", d["ip"]),
            "port": port
        })
    return cameras

def add_cameras_manually():
    cameras = []
    print(Fore.YELLOW + "\nEnter cameras to monitor.")
    print("Format: IP,Name,Port")
    print("Example: 192.168.1.100,Camera1,80")
    print("Type 'done' when finished.\n")
    while True:
        entry = input("Camera: ").strip()
        if entry.lower() == "done":
            break
        parts = entry.split(",")
        if len(parts) >= 2:
            cameras.append({
                "ip": parts[0].strip(),
                "name": parts[1].strip(),
                "port": int(parts[2].strip()) if len(parts) > 2 else 80
            })
            print(Fore.GREEN + "[+] Added: " + parts[0].strip())
        else:
            print(Fore.RED + "[-] Use format: IP,Name,Port")
    return cameras

# ─── Main ─────────────────────────────────────────────────

def main():
    print_banner()

    print(Fore.WHITE + "\nHow do you want to load cameras?")
    print("1. Load from last scan")
    print("2. Add cameras manually")
    print("3. Both")
    choice = input("\nEnter choice (1/2/3): ").strip()

    cameras = []

    if choice in ["1", "3"]:
        scanned = load_cameras_from_scan()
        cameras.extend(scanned)
        print(Fore.GREEN + "[+] Loaded " + str(len(scanned)) + " cameras.")

    if choice in ["2", "3"]:
        manual = add_cameras_manually()
        cameras.extend(manual)

    if not cameras:
        print(Fore.RED + "[-] No cameras to monitor.")
        return

    print(Fore.YELLOW + "\n[*] Starting monitor for " +
          str(len(cameras)) + " cameras...")
    print(Fore.YELLOW + "[*] Checking every 30 seconds.")
    print(Fore.YELLOW + "[*] Dashboard updates every 10 seconds.")
    print(Fore.YELLOW + "[*] Press Ctrl+C to stop.\n")

    time.sleep(2)

    for camera in cameras:
        t = threading.Thread(target=monitor_camera, args=(camera,))
        t.daemon = True
        t.start()

    time.sleep(3)

    dashboard_thread = threading.Thread(target=print_dashboard)
    dashboard_thread.daemon = True
    dashboard_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n[*] Stopping monitor...")
        save_report()
        print(Fore.CYAN + "[+] Goodbye.")

main()