import smtplib
import requests
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ─── Config File ──────────────────────────────────────────

CONFIG_FILE = "alerts_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": ""
        },
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": ""
        }
    }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print("[Alerts] Config saved.")

# ─── Email Alerts ─────────────────────────────────────────

def send_email_alert(subject, body, config=None):
    if config is None:
        config = load_config()

    email_cfg = config.get("email", {})
    if not email_cfg.get("enabled"):
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = email_cfg["sender_email"]
        msg['To'] = email_cfg["recipient_email"]
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(
            email_cfg["smtp_server"],
            email_cfg["smtp_port"]
        )
        server.starttls()
        server.login(
            email_cfg["sender_email"],
            email_cfg["sender_password"]
        )
        server.send_message(msg)
        server.quit()
        print("[Email] Alert sent: " + subject)
        return True
    except Exception as e:
        print("[Email] Failed: " + str(e))
        return False

# ─── Telegram Alerts ──────────────────────────────────────

def send_telegram_alert(message, config=None):
    if config is None:
        config = load_config()

    tg_cfg = config.get("telegram", {})
    if not tg_cfg.get("enabled"):
        return False

    bot_token = tg_cfg.get("bot_token", "")
    chat_id = tg_cfg.get("chat_id", "")

    if not bot_token or not chat_id:
        print("[Telegram] Bot token or chat ID missing.")
        return False

    try:
        url = "https://api.telegram.org/bot" + bot_token + "/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[Telegram] Alert sent.")
            return True
        else:
            print("[Telegram] Failed: " + str(response.text))
            return False
    except Exception as e:
        print("[Telegram] Error: " + str(e))
        return False

# ─── Combined Alert ───────────────────────────────────────

def send_alert(camera_name, ip, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status == "offline":
        subject = "🚨 CCTV Alert: " + camera_name + " is OFFLINE"
        body = (
            "CCTV Sentinel Alert\n"
            "==================\n"
            "Camera:    " + camera_name + "\n"
            "IP:        " + ip + "\n"
            "Status:    OFFLINE\n"
            "Time:      " + timestamp + "\n\n"
            "Please check your camera immediately.\n"
            "This is an automated alert from CCTV Sentinel."
        )
        tg_message = (
            "🚨 <b>CCTV ALERT</b>\n"
            "Camera <b>" + camera_name + "</b> is OFFLINE\n"
            "IP: " + ip + "\n"
            "Time: " + timestamp
        )
    else:
        subject = "✅ CCTV Alert: " + camera_name + " is back ONLINE"
        body = (
            "CCTV Sentinel Alert\n"
            "==================\n"
            "Camera:    " + camera_name + "\n"
            "IP:        " + ip + "\n"
            "Status:    ONLINE\n"
            "Time:      " + timestamp + "\n\n"
            "Camera has recovered.\n"
            "This is an automated alert from CCTV Sentinel."
        )
        tg_message = (
            "✅ <b>CCTV RECOVERY</b>\n"
            "Camera <b>" + camera_name + "</b> is back ONLINE\n"
            "IP: " + ip + "\n"
            "Time: " + timestamp
        )

    config = load_config()
    send_email_alert(subject, body, config)
    send_telegram_alert(tg_message, config)

# ─── Setup Wizard ─────────────────────────────────────────

def setup_alerts():
    print("\n" + "=" * 50)
    print("   CCTV Sentinel — Alert Setup")
    print("=" * 50)

    config = load_config()

    print("\n1. Email Alerts Setup")
    print("-" * 30)
    enable_email = input("Enable email alerts? (y/n): ").strip().lower()

    if enable_email == "y":
        config["email"]["enabled"] = True
        config["email"]["sender_email"] = input(
            "Your Gmail address: ").strip()
        config["email"]["sender_password"] = input(
            "Your Gmail app password: ").strip()
        config["email"]["recipient_email"] = input(
            "Send alerts to (email): ").strip()
        print("[Email] Email alerts configured.")
    else:
        config["email"]["enabled"] = False

    print("\n2. Telegram Alerts Setup")
    print("-" * 30)
    print("To use Telegram alerts:")
    print("  1. Open Telegram and search for @BotFather")
    print("  2. Send /newbot and follow instructions")
    print("  3. Copy the bot token BotFather gives you")
    print("  4. Send a message to your bot")
    print("  5. Visit: api.telegram.org/bot<TOKEN>/getUpdates")
    print("  6. Find your chat_id in the response")

    enable_tg = input("\nEnable Telegram alerts? (y/n): ").strip().lower()

    if enable_tg == "y":
        config["telegram"]["enabled"] = True
        config["telegram"]["bot_token"] = input(
            "Bot token: ").strip()
        config["telegram"]["chat_id"] = input(
            "Chat ID: ").strip()
        print("[Telegram] Telegram alerts configured.")
    else:
        config["telegram"]["enabled"] = False

    save_config(config)

    print("\n[*] Testing alerts...")
    send_alert("TestCamera", "192.168.1.100", "offline")
    print("\n[+] Setup complete.")

if __name__ == "__main__":
    setup_alerts()