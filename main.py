import os
import sys
from database import init_db, load_cameras, save_camera, delete_camera, get_recent_events
from auth import login
from alerts import setup_alerts, send_alert
from scheduler import start_scheduler

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    print("=" * 60)
    print("   CCTV SENTINEL — Professional Edition")
    print("   Phase 4 — Full Feature System")
    print("=" * 60)

def main_menu():
    while True:
        clear()
        print_banner()
        print("\nMain Menu:")
        print("1. Launch GUI Dashboard")
        print("2. Run Network Scanner")
        print("3. Start Uptime Monitor (terminal)")
        print("4. Schedule Automatic Scans")
        print("5. Setup Alerts (Email/Telegram)")
        print("6. View Camera Database")
        print("7. View Recent Events")
        print("8. Exit")

        choice = input("\nEnter choice (1-8): ").strip()

        if choice == "1":
            print("\n[*] Launching GUI...")
            os.system("python gui.py")

        elif choice == "2":
            print("\n[*] Launching Scanner...")
            os.system("python sentinel.py")

        elif choice == "3":
            print("\n[*] Launching Monitor...")
            os.system("python monitor.py")

        elif choice == "4":
            print("\n[*] Launching Scheduler...")
            start_scheduler()

        elif choice == "5":
            setup_alerts()

        elif choice == "6":
            clear()
            print_banner()
            print("\n--- Camera Database ---")
            cameras = load_cameras()
            if not cameras:
                print("No cameras in database.")
            else:
                print("{:<20} {:<16} {:<6} {:<15}".format(
                    "Name", "IP", "Port", "Location"))
                print("-" * 60)
                for cam in cameras:
                    print("{:<20} {:<16} {:<6} {:<15}".format(
                        cam["name"], cam["ip"],
                        str(cam["port"]), cam["location"]
                    ))
            print("\nOptions:")
            print("1. Add camera")
            print("2. Delete camera")
            print("3. Back")
            db_choice = input("\nChoice: ").strip()

            if db_choice == "1":
                ip = input("IP address: ").strip()
                name = input("Camera name: ").strip()
                port = input("Port (default 80): ").strip()
                location = input("Location: ").strip()
                port = int(port) if port else 80
                location = location if location else "Unknown"
                save_camera(ip, name, port, location)
                print("[+] Camera saved: " + name)

            elif db_choice == "2":
                ip = input("IP to delete: ").strip()
                delete_camera(ip)
                print("[+] Camera deleted: " + ip)

            input("\nPress Enter to continue...")

        elif choice == "7":
            clear()
            print_banner()
            print("\n--- Recent Events ---")
            events = get_recent_events(20)
            if not events:
                print("No events recorded yet.")
            else:
                print("{:<15} {:<16} {:<15} {:<25}".format(
                    "Camera", "IP", "Event", "Time"))
                print("-" * 70)
                for event in events:
                    print("{:<15} {:<16} {:<15} {:<25}".format(
                        event[0], event[1], event[2], event[3][:19]
                    ))
            input("\nPress Enter to continue...")

        elif choice == "8":
            print("\nGoodbye.")
            sys.exit(0)

        else:
            print("Invalid choice.")
            input("Press Enter to continue...")

# ─── Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    print_banner()
    print("\n[*] Initializing database...")
    init_db()

    print("[*] Authenticating...")
    if not login():
        print("[-] Access denied. Exiting.")
        sys.exit(1)

    main_menu()