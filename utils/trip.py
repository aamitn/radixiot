import RPi.GPIO as GPIO
import time
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ---------------- Configuration ----------------
TRIP_PIN = 17  # BCM numbering → Physical Pin 11
API_ENDPOINT = "http://localhost:8000/trip"
EMAIL_FROM = "sender@example.com"
EMAIL_TO = "recipient@example.com"
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587
SMTP_USER = "sender@example.com"
SMTP_PASS = "your_password"
POLL_INTERVAL = 0.5  # seconds
# ------------------------------------------------

# Setup GPIO with pull-down
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # default LOW

prev_state = GPIO.input(TRIP_PIN)

def send_email(subject: str, body: str):
    msg = MIMEText(body)
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[EMAIL SENT] {subject}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

def notify_api(status: str):
    try:
        data = {"status": status, "timestamp": datetime.now().isoformat()}
        response = requests.post(API_ENDPOINT, json=data, timeout=5)
        print(f"[API] Sent {status}, Response: {response.status_code}")
    except Exception as e:
        print(f"[API ERROR] {e}")

print("Monitoring trip pin... Press Ctrl+C to exit.")

try:
    while True:
        state = GPIO.input(TRIP_PIN)
        if state != prev_state:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if state == GPIO.HIGH:
                # Trip pin HIGH → healthy
                print(f"[HEALTHY] {timestamp}")
                notify_api("HEALTHY")
            else:
                # Trip pin LOW → grounded / trip
                print(f"[TRIP] {timestamp}")
                send_email("TRIP ALERT", f"Trip pin grounded at {timestamp}")
                notify_api("TRIP")
            prev_state = state
        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("Exiting program.")

finally:
    GPIO.cleanup()
