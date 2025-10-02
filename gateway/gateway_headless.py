import sys
import json
import time
import requests
import os
from datetime import datetime
import pandas as pd
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import logging
import asyncio
import websockets
from ftplib import FTP
import zipfile
import tempfile

# Set up basic logging for terminal output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==============================
# DEFAULT SETTINGS
# ==============================

# Default Modbus Connection Settings
MODBUS_SETTINGS = {
    'host': '192.168.51.201',
    'port': 502,
    'timeout': 3,
    'register_start': 0,
    'num_channels': 8,
    'poll_interval': 5000, # POLL INTERVAL in ms
    'device_id': 'radix-umx201'
}

# Default Channel Names
CHANNEL_NAMES = [f"T{i+1}" for i in range(MODBUS_SETTINGS['num_channels'])] # T1, T2, ..., T8

# Default API Settings
API_SETTINGS = {
    'enabled': True,
    'base_url': 'http://localhost:8000',
    'method': 'POST',
    'timeout': 10,
    'headers': '{"Content-Type": "application/json"}',
    'auth_type': 'none',
    'api_key': '',
    'username': '',
    'password': ''
}

# Default Excel Logging Settings
LOGGING_SETTINGS = {
    'enabled': False,
    'file_path': os.path.join(os.getcwd(), 'temperature_data.xlsx'),
    'log_interval': 'every_poll', # 'every_poll', 'custom'
    'custom_interval': 60, # seconds
    'max_rows': 10000,
    'include_raw_data': True,
    'auto_backup': False,
    'backup_interval': 24 # hours
}

# Default WebSocket Settings
WEBSOCKET_SETTINGS = {
    'enabled': True, # required for both data sending and ftp fetch 
    'server_url': 'ws://localhost:8765'
}

# Default FTP Settings
FTP_SETTINGS = {
    'host': '192.168.51.201',
    'username': 'admin',
    'password': '111',
    'timeout': 10,
    'ws_fetch_enabled': True,
    'ws_fetch_url': 'ws://localhost:8765' # required for ftp-fetch
}

# ==============================
# MODBUS CONNECTION MANAGER 
# ==============================
class ModbusConnectionManager:
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.is_connected = False
        
    def connect(self):
        """Establish connection to Modbus device."""
        if self.is_connected and self.client and self.client.is_socket_open():
            return True
            
        self.disconnect() # Ensure previous connection is closed
        
        try:
            self.client = ModbusTcpClient(
                host=self.settings['host'], 
                port=self.settings['port'], 
                timeout=self.settings['timeout']
            )
            
            if self.client.connect():
                self.is_connected = True
                logger.info(f"Successfully connected to Modbus device at {self.settings['host']}:{self.settings['port']}")
                return True
            else:
                self.client = None
                self.is_connected = False
                logger.error(f"Failed to connect to {self.settings['host']}:{self.settings['port']}")
                return False
                
        except Exception as e:
            self.client = None
            self.is_connected = False
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close connection to Modbus device."""
        if self.client:
            try:
                self.client.close()
            except:
                pass
            finally:
                self.client = None
                self.is_connected = False
                logger.info("Modbus client disconnected.")

    def read_registers(self):
        """Read holding registers from connected device."""
        if not self.is_connected or not self.client:
            raise ConnectionError("Not connected to Modbus device")
            
        try:
            # The UMX201 device uses function code 3 (Read Holding Registers)
            rr = self.client.read_holding_registers(
                address=self.settings['register_start'],
                count=self.settings['num_channels']
            )
            
            if rr.isError():
                raise ModbusException(f"Modbus read error: {rr}")
                
            return rr.registers
            
        except Exception as e:
            self.is_connected = False
            raise

# ==============================
# API SENDER (Refactored to a function)
# ==============================
def send_api_data(payload, api_settings):
    if not api_settings['enabled']:
        return None, None

    try:
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        if api_settings['headers']:
            try:
                custom_headers = json.loads(api_settings['headers'])
                headers.update(custom_headers)
            except json.JSONDecodeError:
                logger.error("Invalid headers JSON format for API payload.")
                return False, "Invalid headers JSON format"

        # Prepare authentication
        auth = None
        if api_settings['auth_type'] == 'basic':
            auth = (api_settings['username'], api_settings['password'])
        elif api_settings['auth_type'] == 'api_key':
            headers['Authorization'] = f"Bearer {api_settings['api_key']}"

        # Use endpoint constructed directly from base_url
        url = f"{api_settings['base_url']}/data"

        response = requests.request(
            method=api_settings['method'],
            url=url,
            json=payload,
            headers=headers,
            auth=auth,
            timeout=api_settings['timeout']
        )

        if response.status_code in [200, 201, 202, 204]:
            logger.info(f"API success: {response.status_code}")
            return True, f"Success: {response.status_code}"
        else:
            logger.warning(f"API failed (HTTP {response.status_code}): {response.text[:80]}")
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        logger.error("API request timeout.")
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        logger.error("API connection error.")
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return False, f"Request error: {str(e)}"
    except Exception as e:
        logger.error(f"API unexpected error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"

# ==============================
# WEBSOCKET SENDER (Refactored to a function)
# ==============================
async def send_websocket_data(payload, ws_settings):
    if not ws_settings['enabled']:
        return

    try:
        async with websockets.connect(ws_settings['server_url']) as websocket:
            message = json.dumps(payload)
            await websocket.send(message)
            logger.info(f"WebSocket success: Sent data to {ws_settings['server_url']}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# ==============================
# EXCEL LOGGER CLASS (Adapted)
# ==============================
class ExcelLogger:
    def __init__(self, settings, channel_names):
        self.settings = settings
        self.channel_names = channel_names
        self.last_log_time = 0
        self.last_backup_time = time.time()
        self.current_row_count = 0
        
    def should_log(self):
        """Determine if data should be logged based on settings."""
        if not self.settings['enabled']:
            return False
            
        if self.settings['log_interval'] == 'every_poll':
            return True
        elif self.settings['log_interval'] == 'custom':
            current_time = time.time()
            # Log only if the custom interval has passed since the last log
            if current_time - self.last_log_time >= self.settings['custom_interval']:
                return True
                
        return False
        
    def log_data(self, payload, temperatures):
        """Log temperature data to Excel file."""
        if not self.should_log():
            return False
            
        try:
            file_path = self.settings['file_path']
            
            # Check if file needs backup/rotation (only checks max_rows and auto_backup)
            if self.settings['auto_backup']:
                self.check_backup()
                
            # Prepare data row
            timestamp = datetime.fromtimestamp(payload['timestamp'])
            row_data = {
                'Timestamp': timestamp,
                'Device_ID': payload['device_id']
            }
            
            # Add temperature columns
            for channel, temp in zip(self.channel_names, temperatures):
                row_data[f'{channel}_Temperature'] = temp
                
            # Add raw data if enabled
            if self.settings['include_raw_data']:
                for i, raw_val in enumerate(payload['raw_registers']):
                    channel_name = self.channel_names[i] if i < len(self.channel_names) else f'CH{i+1}'
                    row_data[f'{channel_name}_Raw'] = raw_val
                    
            df_new = pd.DataFrame([row_data])
            
            # Logic to append or rotate file
            df_combined = df_new
            file_exists = os.path.exists(file_path)
            
            if file_exists:
                try:
                    df_existing = pd.read_excel(file_path, engine='openpyxl')
                    self.current_row_count = len(df_existing)
                    
                    if self.current_row_count >= self.settings['max_rows']:
                        self.create_backup_file(file_path, 'MAX_ROWS') # Renames current file
                        df_combined = df_new
                        self.current_row_count = 1
                        logger.info(f"Log file rotated due to max row limit. New file created: {file_path}")
                    else:
                        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                        self.current_row_count += 1
                        
                except Exception as e:
                    # If can't read existing file, log error and create new
                    logger.warning(f"Could not read existing Excel file: {e}. Starting a new file.")
                    self.current_row_count = 1
            else:
                self.current_row_count = 1
                
            # Write to Excel
            df_combined.to_excel(file_path, index=False, engine='openpyxl')
            
            self.last_log_time = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Excel logging error: {e}")
            return False
            
    def create_backup_file(self, original_path, reason='AUTO_BACKUP'):
        """Create backup of current file by renaming it."""
        try:
            if not os.path.exists(original_path):
                return
                
            base_name = os.path.splitext(original_path)[0]
            backup_name = f"{base_name}_{reason}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            os.rename(original_path, backup_name)
            logger.info(f"Created backup file: {os.path.basename(backup_name)}")
            
        except Exception as e:
            logger.error(f"Backup creation error: {e}")
            
    def check_backup(self):
        """Check if automatic time-based backup is needed."""
        current_time = time.time()
        # Convert hours to seconds
        backup_interval_seconds = self.settings['backup_interval'] * 3600
        
        if current_time - self.last_backup_time >= backup_interval_seconds:
            self.create_backup_file(self.settings['file_path'])
            self.last_backup_time = current_time

# ==============================
# CORE LOGIC (Headless)
# ==============================

def convert_raw_to_temp(raw_registers):
    """
    Converts 16-bit signed raw register values to floating-point temperatures.
    Assumes the value is scaled by 10 (e.g., 255 -> 25.5).
    """
    temperatures = []
    for raw_val in raw_registers:
        # Convert to signed 16-bit integer
        if raw_val & 0x8000:
            signed_val = raw_val - 0x10000
        else:
            signed_val = raw_val
        
        # Assume scaling by 10
        temp = signed_val / 10.0
        temperatures.append(temp)
    return temperatures

def create_json_payload(raw_registers, temperatures, channel_names, device_id):
    """Generates the JSON payload to be sent to an API endpoint."""
    timestamp = time.time()
    
    # Create the channels list with name and temperature
    channels_data = [
        {"name": name, "temperature": temp}
        for name, temp in zip(channel_names, temperatures)
    ]
    
    payload = {
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).isoformat(),
        "device_id": device_id,
        "channels": [name for name in channel_names], # List of channel names
        "temperatures": temperatures, # List of float temperatures
        "raw_registers": raw_registers, # List of raw register integers
        "data": channels_data # Detailed channel data
    }
    return payload

def fetch_and_send_ftp_files(settings, api_settings):
    """Fetch files from device FTP server, zip them, and send to API."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Connect to FTP
            logger.info(f"Connecting to FTP server at {settings['host']}...")
            ftp = FTP(
                settings['host'],
                timeout=settings['timeout']
            )
            ftp.login(
                settings['username'],
                settings['password']
            )
            
            files = ftp.nlst()
            local_files = []
            
            # Download files
            logger.info("Downloading files...")
            for fname in files:
                local_path = os.path.join(tmpdir, fname)
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {fname}', f.write)
                local_files.append(local_path)
                
            ftp.quit()
            
            # Create zip
            zip_path = os.path.join(tmpdir, 'device_files.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for f in local_files:
                    zipf.write(f, os.path.basename(f))
            
            # Send to API
            logger.info("Sending ZIP file to API...")
            with open(zip_path, 'rb') as zf:
                files = {'file': ('device_files.zip', zf, 'application/zip')}
                headers = {'Authorization': f"Bearer {api_settings.get('api_key','')}"} if api_settings.get('auth_type') == 'api_key' else {}
                
                # Use FTP-specific endpoint
                ftp_endpoint = f"{api_settings['base_url']}/data-ftp"
                
                response = requests.post(
                    ftp_endpoint,
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
            if response.status_code in [200, 201, 202, 204]:
                logger.info("FTP files successfully sent to API")
                return True
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"FTP operation error: {str(e)}")
        return False

async def main_loop():
    """The main application loop for Modbus polling, logging, API sending, and WebSocket streaming."""
    
    # Initialize components
    modbus_manager = ModbusConnectionManager(MODBUS_SETTINGS)
    excel_logger = ExcelLogger(LOGGING_SETTINGS, CHANNEL_NAMES)
    
    # Set up WebSocket listener for FTP fetch commands
    async def listen_for_ftp_command():
        while True:
            try:
                if FTP_SETTINGS['ws_fetch_enabled']:
                    async with websockets.connect(FTP_SETTINGS['ws_fetch_url']) as websocket:
                        logger.info(f"Connected to WebSocket server at {FTP_SETTINGS['ws_fetch_url']}")
                        async for message in websocket:
                            if message == "ftp-fetch":
                                logger.info("Received FTP fetch command")
                                await websocket.send("Starting FTP fetch operation...")
                                if fetch_and_send_ftp_files(FTP_SETTINGS, API_SETTINGS):
                                    await websocket.send("FTP fetch completed successfully")
                                else:
                                    await websocket.send("FTP fetch failed")
            except Exception as e:
                logger.error(f"WebSocket listener error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
    
    # Run WebSocket listener in parallel with main loop
    ws_listener = asyncio.create_task(listen_for_ftp_command())
    
    # Main polling loop
    while True:
        poll_start_time = time.time()
        
        raw_registers = None
        temperatures = None
        
        # 1. Connect and Read Data
        try:
            if not modbus_manager.is_connected:
                modbus_manager.connect()
                if not modbus_manager.is_connected:
                    raise ConnectionError("Connection failed and polling will retry.")

            raw_registers = modbus_manager.read_registers()
            
            # 2. Process Data
            temperatures = convert_raw_to_temp(raw_registers)
            
            # 3. Create JSON Payload
            payload = create_json_payload(
                raw_registers, 
                temperatures, 
                CHANNEL_NAMES, 
                MODBUS_SETTINGS['device_id']
            )
            
            # Log successful read
            temp_summary = ', '.join([f"{n}:{t:.1f}" for n, t in zip(CHANNEL_NAMES, temperatures)])
            logger.info(f"✅ Polling successful. Temperatures: {temp_summary}")
            
            # 4. Excel Logging
            if excel_logger.log_data(payload, temperatures):
                logger.info(f"📂 Logged data to Excel file: {excel_logger.settings['file_path']} (Row: {excel_logger.current_row_count})")

            # 5. Send API Data (non-blocking in a separate function call)
            if API_SETTINGS['enabled']:
                send_api_data(payload, API_SETTINGS)

            # 6. Send WebSocket Data (non-blocking)
            if WEBSOCKET_SETTINGS['enabled']:
                await send_websocket_data(payload, WEBSOCKET_SETTINGS)
            
        except ConnectionError as e:
            logger.error(f"❌ Connection Status: {e}. Retrying connection on next cycle.")
        except ModbusException as e:
            logger.error(f"❌ Modbus Communication Error: {e}. Attempting reconnect.")
            modbus_manager.disconnect()
        except Exception as e:
            logger.error(f"⚠️ An unexpected error occurred: {e}")
            
        # 7. Sleep for the poll interval
        poll_duration = time.time() - poll_start_time
        # Convert ms to seconds
        poll_interval_sec = MODBUS_SETTINGS['poll_interval'] / 1000.0
        
        sleep_time = max(0, poll_interval_sec - poll_duration)
        logger.debug(f"Sleeping for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)

    # Cleanup
    ws_listener.cancel()

if __name__ == '__main__':
    try:
        logger.info("Starting headless Modbus TCP Gateway...")
        logger.info(f"Modbus Target: {MODBUS_SETTINGS['host']}:{MODBUS_SETTINGS['port']} | Poll Interval: {MODBUS_SETTINGS['poll_interval']}ms")
        logger.info(f"Excel Logging Enabled: {LOGGING_SETTINGS['enabled']} | API Sending Enabled: {API_SETTINGS['enabled']} | WebSocket Enabled: {WEBSOCKET_SETTINGS['enabled']}")
        
        asyncio.run(main_loop())
        
    except KeyboardInterrupt:
        logger.info("\nGateway stopped by user (Ctrl+C). Exiting.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal application error: {e}")
        sys.exit(1)