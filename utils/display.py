from RPLCD.i2c import CharLCD
import netifaces
import subprocess
import socket
import psutil
import time
import sys
import traceback
import signal

# ----------------------------
# LCD SETUP
# ----------------------------
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
lcd.clear()

stop_flag = False

def handle_exit(signum, frame):
    global stop_flag
    stop_flag = True
    lcd.clear()
    lcd.write_string("ERROR!".ljust(16))
    lcd.cursor_pos = (1,0)
    lcd.write_string("Program stopped".ljust(16))
    sys.exit(1)

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# ----------------------------
# NETWORK INFO FUNCTIONS
# ----------------------------
def get_default_interface():
    try:
        route = subprocess.check_output("ip route show default", shell=True).decode()
        return route.split()[4]
    except Exception:
        return None

def get_ip_address(ifname):
    try:
        iface_addrs = netifaces.ifaddresses(ifname)
        if netifaces.AF_INET in iface_addrs:
            return iface_addrs[netifaces.AF_INET][0]['addr']
        return None
    except Exception:
        return None

def get_connection_mode(iface):
    if iface and iface.startswith("wlan"):
        try:
            ssid = subprocess.check_output("/usr/sbin/iwgetid -r", shell=True).decode().strip()
            return "WiFi:", ssid if ssid else ""
        except Exception:
            return "WiFi:", ""
    elif iface and iface.startswith("eth"):
        try:
            gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
            router_name = socket.gethostbyaddr(gateway)[0]
            return "Eth:", router_name
        except Exception:
            return "Ethernet:", ""
    else:
        return "No Net:", ""

# ----------------------------
# SERVICE STATUS FUNCTIONS
# ----------------------------
SERVICES = ["radix-trip", "radix-display", "radix-gateway", "radix-backend"]

def get_service_status(service_name):
    try:
        subprocess.check_call(
            ["systemctl", "is-active", "--quiet", service_name]
        )
        return "UP"
    except subprocess.CalledProcessError:
        return "DOWN"
    except Exception:
        return "ERR"

def get_all_service_status():
    statuses = []
    for svc in SERVICES:
        short_name = svc.replace("radix-", "").upper()[:4]
        status = get_service_status(svc)
        statuses.append(f"{short_name}:{status}")
    return " ".join(statuses)

# ----------------------------
# SYSTEM STATS FUNCTIONS
# ----------------------------
def get_system_stats():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime_seconds = time.time() - psutil.boot_time()
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime_str = f"{days}d{hours}h" if days > 0 else f"{hours}h{minutes}m"
    line1 = f"CPU:{cpu}% MEM:{mem}%"
    line2 = f"DSK:{disk}% UP:{uptime_str}"
    return line1, line2

# ----------------------------
# MODBUS STATUS FUNCTIONS
# ----------------------------
MODBUS_IP = "192.168.51.201"
MODBUS_PORT = 502
MODBUS_TIMEOUT = 2
last_modbus_success = None

def get_modbus_status():
    global last_modbus_success
    try:
        start = time.time()
        sock = socket.create_connection((MODBUS_IP, MODBUS_PORT), timeout=MODBUS_TIMEOUT)
        sock.close()
        elapsed = int((time.time() - start) * 1000)
        last_modbus_success = time.strftime("%H:%M:%S")
        return f"CONNECTED {elapsed}ms", last_modbus_success
    except Exception:
        return "DOWN", last_modbus_success or "N/A"

# ----------------------------
# DISPLAY HELPERS
# ----------------------------
def scroll_text(text, width=16, delay=0.3):
    if len(text) <= width:
        yield text.ljust(width)
    else:
        scroll_text_data = text + " " * width
        for i in range(len(scroll_text_data) - width + 1):
            yield scroll_text_data[i:i+width]

# ----------------------------
# MAIN LOOP
# ----------------------------
try:
    page = 0  # 0=Network,1=Services,2=System,3=Modbus
    PAGE_SWITCH_INTERVAL = 15
    last_switch = time.time()
    prev_mode = ""

    while not stop_flag:
        now = time.time()

        # --------------------
        # PAGE 0: NETWORK INFO
        # --------------------
        if page == 0:
            iface = get_default_interface()
            ip = get_ip_address(iface) if iface else None
            mode_prefix, name_part = get_connection_mode(iface) if iface else ("No Net:", "")

            if not ip:
                ip = "No Internet / No IP"

            if mode_prefix != prev_mode:
                lcd.clear()
                prev_mode = mode_prefix

            for snippet in scroll_text(name_part, width=16 - len(mode_prefix)):
                if stop_flag or time.time() - last_switch > PAGE_SWITCH_INTERVAL:
                    break
                lcd.cursor_pos = (0,0)
                lcd.write_string(mode_prefix + snippet)
                time.sleep(0.3)

            for snippet in scroll_text(ip):
                if stop_flag or time.time() - last_switch > PAGE_SWITCH_INTERVAL:
                    break
                lcd.cursor_pos = (1,0)
                lcd.write_string(snippet)
                time.sleep(0.3)

        # --------------------
        # PAGE 1: SERVICE STATUS
        # --------------------
        elif page == 1:
            lcd.clear()
            lcd.cursor_pos = (0,0)
            lcd.write_string("Service Status".center(16))
            time.sleep(1)
            status_text = get_all_service_status()
            for snippet in scroll_text(status_text):
                if stop_flag or time.time() - last_switch > PAGE_SWITCH_INTERVAL:
                    break
                lcd.cursor_pos = (1,0)
                lcd.write_string(snippet)
                time.sleep(0.3)

        # --------------------
        # PAGE 2: SYSTEM STATS
        # --------------------
        elif page == 2:
            lcd.clear()
            line1, line2 = get_system_stats()
            lcd.cursor_pos = (0,0)
            lcd.write_string(line1.ljust(16))
            lcd.cursor_pos = (1,0)
            lcd.write_string(line2.ljust(16))
            time.sleep(5)

        # --------------------
        # PAGE 3: MODBUS STATUS
        # --------------------
        else:
            lcd.clear()
            status_line, last_time = get_modbus_status()
            line1 = f"{MODBUS_IP}"
            line2 = f"{status_line} @{last_time}"
            for snippet1 in scroll_text(line1):
                lcd.cursor_pos = (0,0)
                lcd.write_string(snippet1)
                time.sleep(0.3)
            for snippet2 in scroll_text(line2):
                lcd.cursor_pos = (1,0)
                lcd.write_string(snippet2)
                time.sleep(0.3)

        # --------------------
        # PAGE SWITCHING
        # --------------------
        if time.time() - last_switch > PAGE_SWITCH_INTERVAL:
            page = (page + 1) % 4  # 4 pages total
            last_switch = time.time()
            lcd.clear()

except Exception as e:
    lcd.clear()
    lcd.write_string("ERROR!".ljust(16))
    lcd.cursor_pos = (1,0)
    lcd.write_string("Check logs".ljust(16))
    print("Exception occurred:", e, file=sys.stderr)
    traceback.print_exc()
