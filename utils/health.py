import subprocess
import time
import requests
from datetime import datetime
import atexit
import signal
import sys

# ---------------- Configuration ----------------
SERVICE_NAME = "radix-gateway"
API_ENDPOINT = "https://iradixb.bitmutex.com/gatewayhealth"
POLL_INTERVAL = 2          # seconds between checks
HEARTBEAT_INTERVAL = 5    # seconds between heartbeat notifications
# ------------------------------------------------

prev_status = None
last_heartbeat = 0

# ---------------- Utility Functions ----------------
def log(msg: str):
    """Print message with timestamp for console or syslog."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def get_service_status(service_name: str) -> bool:
    """Return True if service is active, False otherwise."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True
        )
        return result.stdout.strip() == "active"
    except Exception as e:
        log(f"[ERROR] Checking service: {e}")
        return False

def notify_api(status: str):
    """Send status to remote API."""
    try:
        data = {
            "service": SERVICE_NAME,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(API_ENDPOINT, json=data, timeout=5)
        log(f"[API] Sent {status}, Response: {response.status_code}")
    except Exception as e:
        log(f"[API ERROR] {e}")

def send_down_on_exit():
    """Notify API that service is DOWN on program exit."""
    notify_api("DOWN")
    log("[EXIT] Notified API that service is DOWN.")

def handle_exit(signum, frame):
    """Handle termination signals (SIGTERM/SIGINT)."""
    send_down_on_exit()
    sys.exit(0)

# ---------------- Setup Signal Handlers ----------------
atexit.register(send_down_on_exit)          # fallback for normal Python exit
signal.signal(signal.SIGTERM, handle_exit)  # systemd stop
signal.signal(signal.SIGINT, handle_exit)   # Ctrl+C

log(f"Monitoring '{SERVICE_NAME}' service... Press Ctrl+C to exit.")

# ---------------- Main Loop ----------------
try:
    while True:
        is_active = get_service_status(SERVICE_NAME)
        current_status = "UP" if is_active else "DOWN"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Notify on status change
        if current_status != prev_status:
            log(f"[{current_status}] Status changed")
            notify_api(current_status)
            prev_status = current_status

        # Heartbeat notification
        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            log(f"[{current_status}] Heartbeat")
            notify_api(current_status)
            last_heartbeat = time.time()

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    handle_exit(None, None)
