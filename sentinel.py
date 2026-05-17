import socket
import requests
import json
import csv
import os
import threading
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# ─── MAC Vendor Database ──────────────────────────────────

CCTV_VENDORS = {
    "b4:a3:82": "Hikvision",
    "c0:56:e3": "Hikvision",
    "e0:50:8b": "Dahua",
    "10:12:fb": "Dahua",
    "00:80:f0": "Panasonic",
    "00:1a:07": "Axis",
    "00:40:8c": "Axis",
    "d4:68:ba": "Reolink",
    "ec:71:db": "Reolink",
    "00:12:12": "Bosch",
    "00:04:a1": "Avigilon",
    "00:1c:27": "Sony",
    "00:0d:f0": "Amcrest",
    "9c:8e:cd": "Uniview",
}

CCTV_PORTS = [80, 443, 554, 8080, 8443, 8554, 37777, 34567, 9000]

# ─── Banner ───────────────────────────────────────────────

def print_banner():
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "   CCTV SENTINEL — Network Camera Discovery Tool")
    print(Fore.CYAN + "   For authorized use on networks you own only")
    print(Fore.CYAN + "=" * 60)
    print(Fore.YELLOW + "\n⚠️  ETHICAL USE ONLY — Only scan your own network\n")

# ─── Network Info ─────────────────────────────────────────

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

# ─── Port Scanner ─────────────────────────────────────────

def scan_port(ip, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_cctv_ports(ip):
    open_ports = []
    for port in CCTV_PORTS:
        if scan_port(ip, port):
            open_ports.append(port)
    return open_ports

# ─── Device Detection ─────────────────────────────────────

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "Unknown"

def get_vendor_from_mac(mac):
    if not mac or mac == "Unknown":
        return "Unknown"
    prefix = mac.lower()[:8]
    for vendor_prefix, vendor_name in CCTV_VENDORS.items():
        if prefix.startswith(vendor_prefix):
            return vendor_name
    return "Unknown"

def identify_device_type(open_ports):
    if 554 in open_ports or 8554 in open_ports:
        return "IP Camera / NVR"
    if 37777 in open_ports:
        return "Dahua DVR/NVR"
    if 34567 in open_ports:
        return "DVR System"
    if 9000 in open_ports:
        return "Hikvision Device"
    if 80 in open_ports or 8080 in open_ports:
        return "Network Device"
    return "Unknown Device"

def check_rtsp(ip):
    rtsp_paths = [
        "rtsp://" + ip + ":554/stream1",
        "rtsp://" + ip + ":554/live/ch0",
        "rtsp://" + ip + ":554/cam/realmonitor",
        "rtsp://" + ip + ":554/h264/ch1/main/av_stream",
    ]
    if scan_port(ip, 554):
        return rtsp_paths[0]
    return None

def check_web_interface(ip, ports):
    for port in [80, 8080, 443]:
        if port in ports:
            protocol = "https" if port == 443 else "http"
            return protocol + "://" + ip + ":" + str(port)
    return None

# ─── Host Discovery ───────────────────────────────────────

results_lock = threading.Lock()
discovered_devices = []

def scan_host(ip):
    open_ports = scan_cctv_ports(ip)
    if not open_ports:
        return

    hostname = get_hostname(ip)
    device_type = identify_device_type(open_ports)
    rtsp_url = check_rtsp(ip)
    web_url = check_web_interface(ip, open_ports)

    device = {
        "ip": ip,
        "hostname": hostname,
        "device_type": device_type,
        "open_ports": open_ports,
        "rtsp_url": rtsp_url if rtsp_url else "N/A",
        "web_url": web_url if web_url else "N/A",
        "discovered_at": str(datetime.now())
    }

    with results_lock:
        discovered_devices.append(device)
        print(Fore.GREEN + "\n[+] Device Found: " + ip)
        print(Fore.WHITE + "    Hostname:    " + hostname)
        print(Fore.WHITE + "    Type:        " + device_type)
        print(Fore.WHITE + "    Open Ports:  " + str(open_ports))
        if rtsp_url:
            print(Fore.CYAN + "    RTSP Stream: " + rtsp_url)
        if web_url:
            print(Fore.CYAN + "    Web Access:  " + web_url)

def scan_network(subnet, start=1, end=254):
    print(Fore.YELLOW + "\n[*] Scanning network: " + subnet + "0/24")
    print(Fore.YELLOW + "[*] Checking " + str(end - start + 1) +
          " hosts for CCTV devices...")
    print(Fore.YELLOW + "[*] This may take a few minutes...\n")

    threads = []
    for i in range(start, end + 1):
        ip = subnet + str(i)
        t = threading.Thread(target=scan_host, args=(ip,))
        threads.append(t)
        t.start()
        if len(threads) % 50 == 0:
            for t in threads[-50:]:
                t.join()

    for t in threads:
        t.join()

    return discovered_devices

# ─── Save Results ─────────────────────────────────────────

def save_results(devices, filename):
    json_file = filename + ".json"
    with open(json_file, "w") as f:
        json.dump(devices, f, indent=2)
    print(Fore.GREEN + "\n[+] JSON saved: " + json_file)

    csv_file = filename + ".csv"
    if devices:
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=devices[0].keys())
            writer.writeheader()
            writer.writerows(devices)
        print(Fore.GREEN + "[+] CSV saved: " + csv_file)

# ─── Main ─────────────────────────────────────────────────

def main():
    print_banner()

    local_ip = get_local_ip()
    subnet = get_subnet(local_ip)

    print(Fore.WHITE + "Your IP address: " + local_ip)
    print(Fore.WHITE + "Network subnet:  " + subnet + "0/24")

    print(Fore.WHITE + "\nScan options:")
    print("1. Quick scan (ports only, faster)")
    print("2. Full scan (all CCTV ports, slower but thorough)")
    choice = input("\nEnter choice (1/2): ").strip()

    print(Fore.WHITE + "\nScan range:")
    print("1. Full network (1-254)")
    print("2. Custom range")
    range_choice = input("Enter choice (1/2): ").strip()

    start = 1
    end = 254
    if range_choice == "2":
        try:
            start = int(input("Start (1-254): "))
            end = int(input("End (1-254): "))
        except:
            start = 1
            end = 254

    discovered_devices.clear()
    devices = scan_network(subnet, start, end)

    print(Fore.CYAN + "\n" + "=" * 60)
    print(Fore.CYAN + "SCAN COMPLETE")
    print(Fore.CYAN + "=" * 60)
    print(Fore.WHITE + "Total devices found: " + str(len(devices)))

    if devices:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "cctv_scan_" + timestamp
        save_results(devices, filename)
        print(Fore.GREEN + "\n[+] Results saved to: " + filename)
    else:
        print(Fore.YELLOW + "\n[-] No CCTV devices found on this network.")
        print(Fore.YELLOW + "    Make sure you're on the right network.")

    print(Fore.CYAN + "=" * 60)

main()