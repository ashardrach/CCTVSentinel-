import schedule
import time
import threading
import socket
import json
import os
from datetime import datetime
from database import init_db, save_scan_result, save_camera, log_event
from alerts import send_alert

# ─── Scanner ──────────────────────────────────────────────

CCTV_PORTS = [80, 443, 554, 8080, 8554, 37777, 34567, 9000]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_subnet(ip):
    parts = ip.split(".")
    return parts[0] + "." + parts[1] + "." + parts[2] + "."

def ping_port(ip, port, timeout=0.5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_single_host(ip, results, lock):
    open_ports = []
    for port in CCTV_PORTS:
        if ping_port(ip, port):
            open_ports.append(port)
    if open_ports:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = ip

        if 554 in open_ports:
            device_type = "IP Camera / NVR"
        elif 37777 in open_ports:
            device_type = "Dahua DVR/NVR"
        elif 9000 in open_ports:
            device_type = "Hikvision Device"
        else:
            device_type = "Network Device"

        device = {
            "ip": ip,
            "hostname": hostname,
            "device_type": device_type,
            "open_ports": open_ports
        }
        with lock:
            results.append(device)

def run_network_scan(subnets=None):
    print("\n[Scheduler] Running scheduled scan at " +
          str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    if subnets is None:
        local_ip = get_local_ip()
        subnets = [get_subnet(local_ip)]

    all_results = []
    lock = threading.Lock()

    for subnet in subnets:
        print("[Scheduler] Scanning subnet: " + subnet + "0/24")
        threads = []
        for i in range(1, 255):
            ip = subnet + str(i)
            t = threading.Thread(
                target=scan_single_host,
                args=(ip, all_results, lock)
            )
            threads.append(t)
            t.start()
            if len(threads) % 50 == 0:
                for th in threads[-50:]:
                    th.join()
        for t in threads:
            t.join()

    for device in all_results:
        save_scan_result(
            device["ip"],
            device["hostname"],
            device["device_type"],
            device["open_ports"]
        )

    print("[Scheduler] Scan complete. Found " +
          str(len(all_results)) + " devices.")
    return all_results

# ─── Scheduler Setup ──────────────────────────────────────

def start_scheduler(subnets=None):
    print("\n" + "=" * 50)
    print("   CCTV Sentinel — Scheduled Scanner")
    print("=" * 50)

    print("\nSchedule options:")
    print("1. Every 5 minutes")
    print("2. Every 30 minutes")
    print("3. Every hour")
    print("4. Every 6 hours")
    print("5. Every day at specific time")
    print("6. Run once now")

    choice = input("\nEnter choice (1-6): ").strip()

    if choice == "1":
        schedule.every(5).minutes.do(run_network_scan, subnets)
        print("[Scheduler] Scan every 5 minutes.")
    elif choice == "2":
        schedule.every(30).minutes.do(run_network_scan, subnets)
        print("[Scheduler] Scan every 30 minutes.")
    elif choice == "3":
        schedule.every().hour.do(run_network_scan, subnets)
        print("[Scheduler] Scan every hour.")
    elif choice == "4":
        schedule.every(6).hours.do(run_network_scan, subnets)
        print("[Scheduler] Scan every 6 hours.")
    elif choice == "5":
        scan_time = input("Enter time (HH:MM, e.g. 08:00): ").strip()
        schedule.every().day.at(scan_time).do(run_network_scan, subnets)
        print("[Scheduler] Daily scan at " + scan_time)
    elif choice == "6":
        run_network_scan(subnets)
        return

    run_network_scan(subnets)

    print("\n[Scheduler] Running. Press Ctrl+C to stop.\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Scheduler] Stopped.")

if __name__ == "__main__":
    init_db()
    start_scheduler()