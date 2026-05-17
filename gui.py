import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import socket
import threading
import time
import json
import csv
import os
from datetime import datetime
from plyer import notification

# ─── Global State ─────────────────────────────────────────

camera_status = {}
status_lock = threading.Lock()
uptime_log = []
monitoring_active = False

# ─── Network Functions ────────────────────────────────────

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
    for p in [port, 80, 554, 8080]:
        if ping_camera(ip, p):
            return True, p
    return False, None

CCTV_PORTS = [80, 443, 554, 8080, 8443, 8554, 37777, 34567, 9000]

def scan_host(ip, results, lock):
    open_ports = []
    for port in CCTV_PORTS:
        if ping_camera(ip, port, timeout=0.5):
            open_ports.append(port)
    if open_ports:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = ip
        device = {
            "ip": ip,
            "hostname": hostname,
            "open_ports": open_ports
        }
        with lock:
            results.append(device)

# ─── Monitor Function ─────────────────────────────────────

def monitor_camera(ip, name, port, app):
    while monitoring_active:
        online, active_port = check_camera(ip, port)

        with status_lock:
            if ip not in camera_status:
                camera_status[ip] = {
                    "name": name,
                    "ip": ip,
                    "status": "unknown",
                    "uptime_count": 0,
                    "downtime_count": 0,
                    "total_checks": 0,
                    "last_seen": "Never"
                }

            prev = camera_status[ip]["status"]
            camera_status[ip]["total_checks"] += 1

            if online:
                camera_status[ip]["status"] = "online"
                camera_status[ip]["uptime_count"] += 1
                camera_status[ip]["last_seen"] = datetime.now().strftime("%H:%M:%S")
                if prev == "offline":
                    uptime_log.append({
                        "time": str(datetime.now()),
                        "camera": name,
                        "ip": ip,
                        "event": "came_online"
                    })
                    app.add_log(name + " came ONLINE")
                    try:
                        notification.notify(
                            title="CCTV Sentinel",
                            message=name + " is back ONLINE",
                            timeout=5
                        )
                    except:
                        pass
            else:
                camera_status[ip]["status"] = "offline"
                camera_status[ip]["downtime_count"] += 1
                if prev in ["online", "unknown"]:
                    uptime_log.append({
                        "time": str(datetime.now()),
                        "camera": name,
                        "ip": ip,
                        "event": "went_offline"
                    })
                    app.add_log(name + " went OFFLINE")
                    try:
                        notification.notify(
                            title="CCTV Sentinel Alert",
                            message="⚠️ " + name + " is OFFLINE",
                            timeout=10
                        )
                    except:
                        pass

        app.refresh_table()
        time.sleep(30)

# ─── GUI Application ──────────────────────────────────────

class CCTVSentinelApp:

    def __init__(self, root):
        self.root = root
        self.root.title("CCTV Sentinel 🎥")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)
        self.cameras = []
        self.build_ui()
        self.refresh_loop()

    def build_ui(self):
        # Title
        tk.Label(
            self.root,
            text="CCTV Sentinel 🎥",
            font=("Helvetica", 20, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(pady=10)

        # Network info
        self.net_var = tk.StringVar()
        local_ip = get_local_ip()
        self.net_var.set("Your IP: " + local_ip +
                         "   Subnet: " + get_subnet(local_ip) + "0/24")
        tk.Label(
            self.root,
            textvariable=self.net_var,
            font=("Helvetica", 10),
            bg="#1e1e2e",
            fg="#a6adc8"
        ).pack()

        # Button bar
        btn_frame = tk.Frame(self.root, bg="#1e1e2e")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="🔍 Scan Network",
            command=self.scan_network,
            bg="#89b4fa",
            fg="#1e1e2e",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2"
        ).grid(row=0, column=0, padx=6)

        tk.Button(
            btn_frame,
            text="➕ Add Camera",
            command=self.add_camera,
            bg="#a6e3a1",
            fg="#1e1e2e",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2"
        ).grid(row=0, column=1, padx=6)

        tk.Button(
            btn_frame,
            text="🗑 Remove Camera",
            command=self.remove_camera,
            bg="#f38ba8",
            fg="#1e1e2e",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2"
        ).grid(row=0, column=2, padx=6)

        self.monitor_btn = tk.Button(
            btn_frame,
            text="▶ Start Monitor",
            command=self.toggle_monitor,
            bg="#cba6f7",
            fg="#1e1e2e",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2"
        )
        self.monitor_btn.grid(row=0, column=3, padx=6)

        tk.Button(
            btn_frame,
            text="💾 Save Report",
            command=self.save_report,
            bg="#f9e2af",
            fg="#1e1e2e",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2"
        ).grid(row=0, column=4, padx=6)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Scan your network or add cameras manually.")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg="#313244",
            fg="#cdd6f4",
            anchor="w",
            padx=10
        ).pack(fill="x", padx=20)

        # Camera table
        tk.Label(
            self.root,
            text="Camera Status",
            font=("Helvetica", 11, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(pady=(10, 2))

        table_frame = tk.Frame(self.root, bg="#1e1e2e")
        table_frame.pack(fill="both", expand=True, padx=20)

        columns = ("name", "ip", "status", "uptime", "last_seen", "ports")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        self.table.heading("name", text="Camera Name")
        self.table.heading("ip", text="IP Address")
        self.table.heading("status", text="Status")
        self.table.heading("uptime", text="Uptime")
        self.table.heading("last_seen", text="Last Seen")
        self.table.heading("ports", text="Ports")

        self.table.column("name", width=150)
        self.table.column("ip", width=120)
        self.table.column("status", width=100)
        self.table.column("uptime", width=80)
        self.table.column("last_seen", width=100)
        self.table.column("ports", width=150)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background="#313244",
            foreground="#cdd6f4",
            fieldbackground="#313244",
            rowheight=28,
            font=("Helvetica", 10)
        )
        style.configure("Treeview.Heading",
            background="#45475a",
            foreground="#cdd6f4",
            font=("Helvetica", 10, "bold")
        )
        style.map("Treeview",
            background=[("selected", "#89b4fa")],
            foreground=[("selected", "#1e1e2e")]
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.table.tag_configure("online", foreground="#a6e3a1")
        self.table.tag_configure("offline", foreground="#f38ba8")
        self.table.tag_configure("unknown", foreground="#f9e2af")

        # Event log
        tk.Label(
            self.root,
            text="Event Log",
            font=("Helvetica", 11, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(pady=(10, 2))

        log_frame = tk.Frame(self.root, bg="#1e1e2e")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.log_box = tk.Text(
            log_frame,
            height=6,
            font=("Courier", 9),
            bg="#313244",
            fg="#cdd6f4",
            relief="flat",
            state="disabled"
        )
        self.log_box.pack(fill="both", expand=True)

        # Stats bar
        self.stats_var = tk.StringVar()
        self.stats_var.set("Cameras: 0 | Online: 0 | Offline: 0")
        tk.Label(
            self.root,
            textvariable=self.stats_var,
            font=("Helvetica", 9),
            bg="#1e1e2e",
            fg="#a6adc8"
        ).pack(pady=5)

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.root.after(0, self._insert_log, "[" + timestamp + "] " + message)

    def _insert_log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def refresh_table(self):
        self.root.after(0, self._update_table)

    def _update_table(self):
        self.table.delete(*self.table.get_children())
        with status_lock:
            cams = list(camera_status.values())

        online = 0
        offline = 0

        for cam in cams:
            status = cam["status"]
            if status == "online":
                status_text = "🟢 ONLINE"
                tag = "online"
                online += 1
            elif status == "offline":
                status_text = "🔴 OFFLINE"
                tag = "offline"
                offline += 1
            else:
                status_text = "⏳ Checking..."
                tag = "unknown"

            total = cam["total_checks"]
            if total > 0:
                uptime = str(round((cam["uptime_count"] / total) * 100, 1)) + "%"
            else:
                uptime = "N/A"

            cam_data = next((c for c in self.cameras
                            if c["ip"] == cam["ip"]), {})
            ports = str(cam_data.get("open_ports", []))

            self.table.insert("", "end",
                values=(cam["name"], cam["ip"], status_text,
                        uptime, cam["last_seen"], ports),
                tags=(tag,)
            )

        self.stats_var.set(
            "Cameras: " + str(len(cams)) +
            " | Online: " + str(online) +
            " | Offline: " + str(offline)
        )

    def scan_network(self):
        self.status_var.set("Scanning network... Please wait.")
        self.add_log("Network scan started.")

        def do_scan():
            local_ip = get_local_ip()
            subnet = get_subnet(local_ip)
            results = []
            lock = threading.Lock()
            threads = []

            for i in range(1, 255):
                ip = subnet + str(i)
                t = threading.Thread(
                    target=scan_host,
                    args=(ip, results, lock)
                )
                threads.append(t)
                t.start()
                if len(threads) % 50 == 0:
                    for th in threads[-50:]:
                        th.join()

            for t in threads:
                t.join()

            self.root.after(0, self._scan_complete, results)

        threading.Thread(target=do_scan, daemon=True).start()

    def _scan_complete(self, results):
        for device in results:
            if not any(c["ip"] == device["ip"] for c in self.cameras):
                self.cameras.append(device)
                with status_lock:
                    camera_status[device["ip"]] = {
                        "name": device["hostname"],
                        "ip": device["ip"],
                        "status": "unknown",
                        "uptime_count": 0,
                        "downtime_count": 0,
                        "total_checks": 0,
                        "last_seen": "Never"
                    }

        self._update_table()
        self.status_var.set("Scan complete. Found " +
                           str(len(results)) + " devices.")
        self.add_log("Scan complete. Found " +
                    str(len(results)) + " devices.")

    def add_camera(self):
        ip = simpledialog.askstring("Add Camera", "Enter IP address:")
        if not ip:
            return
        name = simpledialog.askstring("Add Camera", "Enter camera name:")
        if not name:
            name = ip

        camera = {"ip": ip, "hostname": name, "open_ports": [80]}
        if not any(c["ip"] == ip for c in self.cameras):
            self.cameras.append(camera)
            with status_lock:
                camera_status[ip] = {
                    "name": name,
                    "ip": ip,
                    "status": "unknown",
                    "uptime_count": 0,
                    "downtime_count": 0,
                    "total_checks": 0,
                    "last_seen": "Never"
                }
            self._update_table()
            self.add_log("Added camera: " + name + " (" + ip + ")")
            self.status_var.set("Camera added: " + name)
        else:
            messagebox.showinfo("Info", "Camera already exists.")

    def remove_camera(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a camera to remove.")
            return
        item = self.table.item(selected[0])
        ip = item["values"][1]
        self.cameras = [c for c in self.cameras if c["ip"] != ip]
        with status_lock:
            if ip in camera_status:
                del camera_status[ip]
        self._update_table()
        self.add_log("Removed camera: " + str(ip))

    def toggle_monitor(self):
        global monitoring_active
        if not monitoring_active:
            if not self.cameras:
                messagebox.showwarning(
                    "Warning",
                    "No cameras to monitor.\nScan network or add cameras first."
                )
                return
            monitoring_active = True
            self.monitor_btn.config(
                text="⏹ Stop Monitor",
                bg="#f38ba8"
            )
            self.status_var.set("Monitoring " +
                               str(len(self.cameras)) + " cameras...")
            self.add_log("Monitoring started.")

            for camera in self.cameras:
                t = threading.Thread(
                    target=monitor_camera,
                    args=(
                        camera["ip"],
                        camera.get("hostname", camera["ip"]),
                        camera.get("open_ports", [80])[0],
                        self
                    )
                )
                t.daemon = True
                t.start()
        else:
            monitoring_active = False
            self.monitor_btn.config(
                text="▶ Start Monitor",
                bg="#cba6f7"
            )
            self.status_var.set("Monitoring stopped.")
            self.add_log("Monitoring stopped.")

    def save_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "gui_report_" + timestamp

        with status_lock:
            data = list(camera_status.values())

        with open(filename + ".json", "w") as f:
            json.dump({
                "cameras": data,
                "events": uptime_log
            }, f, indent=2)

        if uptime_log:
            with open(filename + "_events.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=uptime_log[0].keys())
                writer.writeheader()
                writer.writerows(uptime_log)

        messagebox.showinfo(
            "Saved",
            "Report saved:\n" + filename + ".json"
        )
        self.add_log("Report saved: " + filename)

    def refresh_loop(self):
        self._update_table()
        self.root.after(10000, self.refresh_loop)

# ─── Start ────────────────────────────────────────────────

root = tk.Tk()
app = CCTVSentinelApp(root)
root.mainloop()