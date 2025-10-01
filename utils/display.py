from RPLCD.i2c import CharLCD
import netifaces
import subprocess
import socket
import time
import sys
import traceback
import signal

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
    """Return mode and name separately"""
    if iface and iface.startswith("wlan"):
        try:
            ssid = subprocess.check_output("iwgetid -r", shell=True).decode().strip()
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

def scroll_text(text, width=16, delay=0.3):
    """Yield slices of text for scrolling effect"""
    if len(text) <= width:
        yield text.ljust(width)
    else:
        scroll_text_data = text + " " * width
        for i in range(len(scroll_text_data) - width + 1):
            yield scroll_text_data[i:i+width]

try:
    prev_mode = ""
    prev_ip = ""

    while not stop_flag:
        iface = get_default_interface()
        ip = get_ip_address(iface) if iface else None
        mode_prefix, name_part = get_connection_mode(iface) if iface else ("No Net:", "")

        if not ip:
            ip = "No Internet / No IP"

        # Update first line: static prefix + scrolling name part
        if mode_prefix != prev_mode:
            lcd.clear()
            prev_mode = mode_prefix

        for snippet in scroll_text(name_part, width=16-len(mode_prefix)):
            lcd.cursor_pos = (0,0)
            lcd.write_string(mode_prefix + snippet)
            time.sleep(0.3)

        # Scroll IP on second line
        for snippet in scroll_text(ip):
            lcd.cursor_pos = (1, 0)
            lcd.write_string(snippet)
            time.sleep(0.3)

except Exception as e:
    lcd.clear()
    lcd.write_string("ERROR!".ljust(16))
    lcd.cursor_pos = (1,0)
    lcd.write_string("Check logs".ljust(16))
    print("Exception occurred:", e, file=sys.stderr)
    traceback.print_exc()
