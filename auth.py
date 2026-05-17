import hashlib
import json
import os
import getpass
from datetime import datetime

AUTH_FILE = "auth.json"

# ─── Password Hashing ─────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─── Setup ────────────────────────────────────────────────

def setup_auth():
    print("\n" + "=" * 50)
    print("   CCTV Sentinel — First Time Setup")
    print("=" * 50)
    print("\nCreate your master login credentials.")
    print("This protects access to CCTV Sentinel.\n")

    username = input("Create username: ").strip()
    while len(username) < 3:
        print("Username must be at least 3 characters.")
        username = input("Create username: ").strip()

    password = getpass.getpass("Create password: ")
    while len(password) < 6:
        print("Password must be at least 6 characters.")
        password = getpass.getpass("Create password: ")

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match. Try again.")
        return setup_auth()

    auth_data = {
        "username": username,
        "password_hash": hash_password(password),
        "created_at": str(datetime.now()),
        "last_login": None
    }

    with open(AUTH_FILE, "w") as f:
        json.dump(auth_data, f, indent=2)

    print("\n[+] Account created successfully.")
    print("[+] Username: " + username)
    return True

def load_auth():
    if not os.path.exists(AUTH_FILE):
        return None
    with open(AUTH_FILE, "r") as f:
        return json.load(f)

def save_last_login(auth_data):
    auth_data["last_login"] = str(datetime.now())
    with open(AUTH_FILE, "w") as f:
        json.dump(auth_data, f, indent=2)

# ─── Login ────────────────────────────────────────────────

def login():
    auth_data = load_auth()

    if auth_data is None:
        print("[Auth] No account found. Setting up...")
        setup_auth()
        auth_data = load_auth()

    print("\n" + "=" * 50)
    print("   CCTV Sentinel — Login")
    print("=" * 50)

    if auth_data.get("last_login"):
        print("Last login: " + auth_data["last_login"])

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        print()
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")

        if (username == auth_data["username"] and
                hash_password(password) == auth_data["password_hash"]):
            save_last_login(auth_data)
            print("\n[+] Login successful. Welcome, " + username + "!")
            return True
        else:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print("[-] Incorrect credentials. " +
                      str(remaining) + " attempts remaining.")
            else:
                print("[-] Too many failed attempts. Access denied.")
                return False

    return False

# ─── Change Password ──────────────────────────────────────

def change_password():
    auth_data = load_auth()
    if not auth_data:
        print("[-] No account found.")
        return False

    current = getpass.getpass("Current password: ")
    if hash_password(current) != auth_data["password_hash"]:
        print("[-] Incorrect password.")
        return False

    new_pass = getpass.getpass("New password: ")
    if len(new_pass) < 6:
        print("[-] Password too short.")
        return False

    confirm = getpass.getpass("Confirm new password: ")
    if new_pass != confirm:
        print("[-] Passwords do not match.")
        return False

    auth_data["password_hash"] = hash_password(new_pass)
    with open(AUTH_FILE, "w") as f:
        json.dump(auth_data, f, indent=2)

    print("[+] Password changed successfully.")
    return True

if __name__ == "__main__":
    if login():
        print("\n[+] Access granted to CCTV Sentinel.")
    else:
        print("\n[-] Access denied.")