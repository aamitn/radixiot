#!/usr/bin/env python3
"""
Radix UMX201 Modbus TCP IoT Gateway GUI using PyQt5
Features:
- Connection management (connect/disconnect)
- Connection settings dialog
- Raw Holding Registers display
- Formatted Temperatures display
- Channel Names configuration
- JSON Payload generation
- Auto-polling with manual refresh option
- Real-time temperature graphs
- Excel data logging with configurable options
"""
import sys
import json
import time
import requests
import os
import zipfile
import tempfile
from datetime import datetime
from collections import deque
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QTextEdit, QPushButton, QGroupBox,
                            QLineEdit, QSpinBox, QDialog, QFormLayout,
                            QDialogButtonBox, QCheckBox, QMessageBox, QComboBox,
                            QPlainTextEdit, QTabWidget, QFileDialog, QSplitter,
                            QFrame, QMenuBar, QAction)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot, Qt
from PyQt5.QtGui import QFont, QIcon
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import asyncio
import websockets
from ftplib import FTP

class AutoCloseMessageBox(QMessageBox):
    def __init__(self, parent=None, timeout=10):
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.timeout = timeout
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(timeout * 1000)  # Convert seconds to milliseconds

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()

class AboutDialog(QDialog):
    """A professional, custom 'About' dialog using PyQt5."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        # Set a fixed size for a clean, consistent look
        self.setFixedSize(400, 250)

        # Main layout
        layout = QVBoxLayout(self)

        # --- Content Widgets ---

        # 1. Application Title (Bold and larger font)
        title_label = QLabel("Radix UMX201 Modbus TCP Gateway")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 2. Version
        version_label = QLabel("Version 1.5")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Add a separator line for visual appeal
        layout.addWidget(self._create_separator())

        # 3. Developer Information (Smaller/muted font)
        dev_label = QLabel("Developed by Bitmutex Technologies")
        dev_font = QFont()
        dev_font.setPointSize(9)
        dev_font.setItalic(True)
        dev_label.setFont(dev_font)
        dev_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_label)

        # Add some vertical space
        layout.addSpacing(20)

        # 4. Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        # Center the button
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.addWidget(close_button, alignment=Qt.AlignCenter)
        layout.addWidget(button_container)

        self.setLayout(layout)

    def _create_separator(self):
        """Helper function to create a horizontal line."""
        line = QWidget()
        line.setFixedHeight(1)
        # Use a style sheet for a simple, gray line
        line.setStyleSheet("background-color: #cccccc;")
        return line


# ==============================
# WEBSOCKET SETTINGS DIALOG
# ==============================
class WebSocketSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("WebSocket Settings")
        self.setModal(True)
        self.setFixedSize(400, 200)

        default_settings = {
            'enabled': False,
            #'server_url': 'ws://localhost:8000/ws/gateway',
            'server_url': 'wss://iradixb.bitmutex.com/ws/gateway'
            
        }

        if settings:
            default_settings.update(settings)

        layout = QFormLayout()

        # Enable WebSocket
        self.enabled_checkbox = QCheckBox("Enable WebSocket Streaming")
        self.enabled_checkbox.setChecked(default_settings['enabled'])
        layout.addRow(self.enabled_checkbox)

        # Server URL
        self.server_url_edit = QLineEdit(default_settings['server_url'])
        layout.addRow("WebSocket Server URL:", self.server_url_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_settings(self):
        return {
            'enabled': self.enabled_checkbox.isChecked(),
            'server_url': self.server_url_edit.text().strip()
        }

# ==============================
# WEBSOCKET SENDER THREAD
# ==============================
class WebSocketSenderThread(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, payload, ws_settings):
        super().__init__()
        self.payload = payload
        self.ws_settings = ws_settings
        self.is_running = True

    async def send_data(self, url, message):
        try:
            async with websockets.connect(url) as websocket:
                await websocket.send(message)
                self.success.emit()
        except Exception as e:
            self.error.emit(str(e))

    def run(self):
        if not self.ws_settings['enabled']:
            return

        url = self.ws_settings['server_url']
        message = json.dumps(self.payload)

        # Run the asynchronous function
        asyncio.run(self.send_data(url, message))



# ==============================
# LOGGING SETTINGS DIALOG
# ==============================
class LoggingSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Excel Logging Settings")
        self.setModal(True)
        self.setFixedSize(450, 300)
        
        # Default logging settings
        default_settings = {
            'enabled': False,
            'file_path': os.path.join(os.getcwd(), 'temperature_data.xlsx'),
            'log_interval': 'every_poll',  # 'every_poll', 'custom'
            'custom_interval': 60,  # seconds
            'max_rows': 10000,
            'include_raw_data': True,
            'auto_backup': False,
            'backup_interval': 24  # hours
        }
        
        if settings:
            default_settings.update(settings)
            
        layout = QFormLayout()
        
        # Enable Logging
        self.enabled_checkbox = QCheckBox("Enable Excel Logging")
        self.enabled_checkbox.setChecked(default_settings['enabled'])
        layout.addRow(self.enabled_checkbox)
        
        # File Path Selection
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit(default_settings['file_path'])
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_btn)
        layout.addRow("Excel File Path:", file_layout)
        
        # Log Interval
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['every_poll', 'custom'])
        self.interval_combo.setCurrentText(default_settings['log_interval'])
        self.interval_combo.currentTextChanged.connect(self.on_interval_changed)
        layout.addRow("Log Interval:", self.interval_combo)
        
        # Custom Interval
        self.custom_interval_spin = QSpinBox()
        self.custom_interval_spin.setRange(10, 3600)
        self.custom_interval_spin.setValue(default_settings['custom_interval'])
        self.custom_interval_spin.setSuffix(" seconds")
        self.custom_interval_label = QLabel("Custom Interval:")
        layout.addRow(self.custom_interval_label, self.custom_interval_spin)
        
        # Max Rows
        self.max_rows_spin = QSpinBox()
        self.max_rows_spin.setRange(100, 100000)
        self.max_rows_spin.setValue(default_settings['max_rows'])
        layout.addRow("Max Rows per File:", self.max_rows_spin)
        
        # Include Raw Data
        self.raw_data_checkbox = QCheckBox("Include Raw Register Data")
        self.raw_data_checkbox.setChecked(default_settings['include_raw_data'])
        layout.addRow(self.raw_data_checkbox)
        
        # Auto Backup
        self.backup_checkbox = QCheckBox("Enable Auto Backup")
        self.backup_checkbox.setChecked(default_settings['auto_backup'])
        self.backup_checkbox.stateChanged.connect(self.on_backup_changed)
        layout.addRow(self.backup_checkbox)
        
        # Backup Interval
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 168)
        self.backup_interval_spin.setValue(default_settings['backup_interval'])
        self.backup_interval_spin.setSuffix(" hours")
        self.backup_interval_label = QLabel("Backup Interval:")
        layout.addRow(self.backup_interval_label, self.backup_interval_spin)
        
        # Update field visibility
        self.on_interval_changed(default_settings['log_interval'])
        self.on_backup_changed(default_settings['auto_backup'])
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", self.file_path_edit.text(),
            "Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            
    def on_interval_changed(self, interval_type):
        show_custom = interval_type == 'custom'
        self.custom_interval_label.setVisible(show_custom)
        self.custom_interval_spin.setVisible(show_custom)
        
    def on_backup_changed(self, state):
        show_backup = state == 2  # Qt.Checked
        self.backup_interval_label.setVisible(show_backup)
        self.backup_interval_spin.setVisible(show_backup)
        
    def get_settings(self):
        return {
            'enabled': self.enabled_checkbox.isChecked(),
            'file_path': self.file_path_edit.text().strip(),
            'log_interval': self.interval_combo.currentText(),
            'custom_interval': self.custom_interval_spin.value(),
            'max_rows': self.max_rows_spin.value(),
            'include_raw_data': self.raw_data_checkbox.isChecked(),
            'auto_backup': self.backup_checkbox.isChecked(),
            'backup_interval': self.backup_interval_spin.value()
        }

# ==============================
# REAL-TIME GRAPH WIDGET
# ==============================
class TemperatureGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.channel_names = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
        self.max_points = 100  # Maximum points to display
        self.data_buffer = {}  # Channel name -> deque of (timestamp, temperature)
        self.colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        # Initialize data buffers
        for channel in self.channel_names:
            self.data_buffer[channel] = deque(maxlen=self.max_points)
            
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Graph controls
        controls_layout = QHBoxLayout()
        
        self.auto_scale_checkbox = QCheckBox("Auto Scale Y-axis")
        self.auto_scale_checkbox.setChecked(True)
        
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.stateChanged.connect(self.toggle_grid)
        
        self.legend_checkbox = QCheckBox("Show Legend")
        self.legend_checkbox.setChecked(True)
        self.legend_checkbox.stateChanged.connect(self.toggle_legend)
        
        self.clear_btn = QPushButton("Clear Data")
        self.clear_btn.clicked.connect(self.clear_data)
        
        controls_layout.addWidget(self.auto_scale_checkbox)
        controls_layout.addWidget(self.grid_checkbox)
        controls_layout.addWidget(self.legend_checkbox)
        controls_layout.addStretch()
        controls_layout.addWidget(self.clear_btn)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Configure plot
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.set_title('Real-time Temperature Monitoring')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        
        # Format x-axis for time display
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
        
        self.figure.tight_layout()
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
    def update_channel_names(self, names):
        """Update channel names when configuration changes."""
        self.channel_names = names[:len(self.colors)]  # Limit to available colors
        
        # Clear and reinitialize buffers
        self.data_buffer.clear()
        for channel in self.channel_names:
            self.data_buffer[channel] = deque(maxlen=self.max_points)
            
        self.clear_plot()
        
    def add_data_point(self, temperatures):
        """Add new temperature data point."""
        timestamp = datetime.now()
        
        # Add data to buffers
        for i, (channel, temp) in enumerate(zip(self.channel_names, temperatures)):
            if i < len(temperatures):
                self.data_buffer[channel].append((timestamp, temp))
                
        self.update_plot()
        
    def update_plot(self):
        """Refresh the plot with current data."""
        self.ax.clear()
        
        # Plot each channel
        for i, channel in enumerate(self.channel_names):
            if self.data_buffer[channel]:
                timestamps, temps = zip(*self.data_buffer[channel])
                color = self.colors[i % len(self.colors)]
                self.ax.plot(timestamps, temps, 
                           label=f'{channel}: {temps[-1]:.1f}°C',
                           color=color, marker='o', markersize=2, linewidth=1.5)
        
        # Configure plot
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.set_title('Real-time Temperature Monitoring')
        
        if self.grid_checkbox.isChecked():
            self.ax.grid(True, alpha=0.3)
            
        if self.legend_checkbox.isChecked() and self.data_buffer:
            self.ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        
        # Format x-axis
        if any(self.data_buffer.values()):
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.figure.autofmt_xdate()
            
        # Auto-scale or set fixed range
        if self.auto_scale_checkbox.isChecked():
            self.ax.relim()
            self.ax.autoscale_view()
        else:
            # Set reasonable temperature range
            self.ax.set_ylim(0, 100)
            
        self.figure.tight_layout()
        self.canvas.draw()
        
    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.set_title('Real-time Temperature Monitoring')
        if self.grid_checkbox.isChecked():
            self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()
        
    def clear_data(self):
        """Clear all data buffers and plot."""
        for buffer in self.data_buffer.values():
            buffer.clear()
        self.clear_plot()
        
    def toggle_grid(self, state):
        """Toggle grid visibility."""
        self.update_plot()
        
    def toggle_legend(self, state):
        """Toggle legend visibility."""
        self.update_plot()

# ==============================
# EXCEL LOGGER CLASS
# ==============================
class ExcelLogger:
    def __init__(self):
        self.settings = {
            'enabled': False,
            'file_path': os.path.join(os.getcwd(), 'temperature_data.xlsx'),
            'log_interval': 'every_poll',
            'custom_interval': 60,
            'max_rows': 10000,
            'include_raw_data': True,
            'auto_backup': False,
            'backup_interval': 24
        }
        self.last_log_time = 0
        self.last_backup_time = time.time()
        self.current_row_count = 0
        
    def update_settings(self, new_settings):
        """Update logger settings."""
        self.settings.update(new_settings)
        
    def should_log(self):
        """Determine if data should be logged based on settings."""
        if not self.settings['enabled']:
            return False
            
        if self.settings['log_interval'] == 'every_poll':
            return True
        elif self.settings['log_interval'] == 'custom':
            current_time = time.time()
            if current_time - self.last_log_time >= self.settings['custom_interval']:
                return True
                
        return False
        
    def log_data(self, payload, temperatures):
        """Log temperature data to Excel file."""
        if not self.should_log():
            return False
            
        try:
            file_path = self.settings['file_path']
            
            # Check if file needs backup/rotation
            if self.settings['auto_backup']:
                self.check_backup()
                
            # Prepare data row
            timestamp = datetime.fromtimestamp(payload['timestamp'])
            row_data = {
                'Timestamp': timestamp,
                'Device_ID': payload['device_id']
            }
            
            # Add temperature columns
            for i, (channel, temp) in enumerate(zip(payload['channels'], temperatures)):
                row_data[f'{channel}_Temperature'] = temp
                
            # Add raw data if enabled
            if self.settings['include_raw_data']:
                for i, raw_val in enumerate(payload['raw_registers']):
                    channel_name = payload['channels'][i] if i < len(payload['channels']) else f'CH{i+1}'
                    row_data[f'{channel_name}_Raw'] = raw_val
                    
            # Create DataFrame
            df_new = pd.DataFrame([row_data])
            
            # Check if file exists
            if os.path.exists(file_path):
                # Read existing data
                try:
                    df_existing = pd.read_excel(file_path, engine='openpyxl')
                    self.current_row_count = len(df_existing)
                    
                    # Check if we need to create a new file (max rows reached)
                    if self.current_row_count >= self.settings['max_rows']:
                        self.create_backup_file(file_path)
                        df_combined = df_new
                        self.current_row_count = 1
                    else:
                        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                        self.current_row_count += 1
                        
                except Exception as e:
                    # If can't read existing file, create new
                    df_combined = df_new
                    self.current_row_count = 1
            else:
                df_combined = df_new
                self.current_row_count = 1
                
            # Write to Excel
            df_combined.to_excel(file_path, index=False, engine='openpyxl')
            
            self.last_log_time = time.time()
            return True
            
        except Exception as e:
            print(f"Excel logging error: {e}")
            return False
            
    def create_backup_file(self, original_path):
        """Create backup of current file."""
        try:
            base_name = os.path.splitext(original_path)[0]
            backup_name = f"{base_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            if os.path.exists(original_path):
                os.rename(original_path, backup_name)
                
        except Exception as e:
            print(f"Backup creation error: {e}")
            
    def check_backup(self):
        """Check if automatic backup is needed."""
        current_time = time.time()
        backup_interval_seconds = self.settings['backup_interval'] * 3600
        
        if current_time - self.last_backup_time >= backup_interval_seconds:
            self.create_backup_file(self.settings['file_path'])
            self.last_backup_time = current_time

# ==============================
# API SETTINGS DIALOG (unchanged)
# ==============================
class ApiSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("API Settings")
        self.setModal(True)
        self.setFixedSize(400, 350)
        
        # Default API settings
        default_settings = {
            'enabled': False,
            #'base_url': 'http://localhost:8000',  # Changed to base URL
            'base_url': 'https://iradixb.bitmutex.com',
            'method': 'POST',
            'timeout': 10,
            'headers': '{"Content-Type": "application/json"}',
            'auth_type': 'none',
            'api_key': '',
            'username': '',
            'password': ''
        }
        
        if settings:
            default_settings.update(settings)
            
        layout = QFormLayout()
        
        # Enable API
        self.enabled_checkbox = QCheckBox("Enable API Sending")
        self.enabled_checkbox.setChecked(default_settings['enabled'])
        layout.addRow(self.enabled_checkbox)
        
        # API Endpoint
        self.endpoint_edit = QLineEdit(default_settings['base_url'])
        layout.addRow("API Base URL:", self.endpoint_edit)
        
        # HTTP Method
        self.method_combo = QComboBox()
        self.method_combo.addItems(['POST', 'PUT', 'PATCH'])
        self.method_combo.setCurrentText(default_settings['method'])
        layout.addRow("HTTP Method:", self.method_combo)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(default_settings['timeout'])
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Request Timeout:", self.timeout_spin)
        
        # Headers
        self.headers_edit = QPlainTextEdit(default_settings['headers'])
        self.headers_edit.setFixedHeight(60)
        layout.addRow("Headers (JSON):", self.headers_edit)
        
        # Authentication Type
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(['none', 'api_key', 'basic'])
        self.auth_combo.setCurrentText(default_settings['auth_type'])
        self.auth_combo.currentTextChanged.connect(self.on_auth_changed)
        layout.addRow("Authentication:", self.auth_combo)
        
        # API Key
        self.api_key_edit = QLineEdit(default_settings['api_key'])
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_label = QLabel("API Key:")
        layout.addRow(self.api_key_label, self.api_key_edit)
        
        # Username
        self.username_edit = QLineEdit(default_settings['username'])
        self.username_label = QLabel("Username:")
        layout.addRow(self.username_label, self.username_edit)
        
        # Password
        self.password_edit = QLineEdit(default_settings['password'])
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_label = QLabel("Password:")
        layout.addRow(self.password_label, self.password_edit)
        
        # Update auth fields visibility
        self.on_auth_changed(default_settings['auth_type'])
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
    def on_auth_changed(self, auth_type):
        # Show/hide auth fields based on selection
        show_api_key = auth_type == 'api_key'
        show_basic = auth_type == 'basic'
        
        self.api_key_label.setVisible(show_api_key)
        self.api_key_edit.setVisible(show_api_key)
        
        self.username_label.setVisible(show_basic)
        self.username_edit.setVisible(show_basic)
        self.password_label.setVisible(show_basic)
        self.password_edit.setVisible(show_basic)
        
    def get_settings(self):
        return {
            'enabled': self.enabled_checkbox.isChecked(),
            'base_url': self.endpoint_edit.text().strip(),
            'method': self.method_combo.currentText(),
            'timeout': self.timeout_spin.value(),
            'headers': self.headers_edit.toPlainText().strip(),
            'auth_type': self.auth_combo.currentText(),
            'api_key': self.api_key_edit.text().strip(),
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text().strip()
        }

# ==============================
# CONNECTION SETTINGS DIALOG (unchanged)
# ==============================
class ConnectionSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Modbus Connection Settings")
        self.setModal(True)
        self.setFixedSize(300, 280)
        
        # Default settings
        default_settings = {
            'host': '192.168.51.201',
            'port': 502,
            'timeout': 3,
            'register_start': 0,
            'num_channels': 8,
            'poll_interval': 5000,
            'device_id': 'radix-umx201'
        }
        
        if settings:
            default_settings.update(settings)
            
        layout = QFormLayout()
        
        # Host
        self.host_edit = QLineEdit(default_settings['host'])
        layout.addRow("Host/IP Address:", self.host_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(default_settings['port'])
        layout.addRow("Port:", self.port_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 30)
        self.timeout_spin.setValue(default_settings['timeout'])
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Timeout:", self.timeout_spin)
        
        # Register Start
        self.register_start_spin = QSpinBox()
        self.register_start_spin.setRange(0, 65535)
        self.register_start_spin.setValue(default_settings['register_start'])
        layout.addRow("Register Start:", self.register_start_spin)
        
        # Number of Channels
        self.num_channels_spin = QSpinBox()
        self.num_channels_spin.setRange(1, 32)
        self.num_channels_spin.setValue(default_settings['num_channels'])
        layout.addRow("Number of Channels:", self.num_channels_spin)
        
        # Poll Interval
        self.poll_interval_spin = QSpinBox()
        self.poll_interval_spin.setRange(200, 60000)  # POLL INTERVAL RANGE
        self.poll_interval_spin.setValue(default_settings['poll_interval'])
        self.poll_interval_spin.setSuffix(" ms")
        layout.addRow("Poll Interval:", self.poll_interval_spin)
        
        # Device ID
        self.device_id_edit = QLineEdit(default_settings['device_id'])
        layout.addRow("Device ID:", self.device_id_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_settings(self):
        return {
            'host': self.host_edit.text().strip(),
            'port': self.port_spin.value(),
            'timeout': self.timeout_spin.value(),
            'register_start': self.register_start_spin.value(),
            'num_channels': self.num_channels_spin.value(),
            'poll_interval': self.poll_interval_spin.value(),
            'device_id': self.device_id_edit.text().strip()
        }

# ==============================
# API SENDER THREAD (unchanged)
# ==============================
class ApiSenderThread(QThread):
    response_received = pyqtSignal(bool, str, int)  # success, message, status_code
    
    def __init__(self, payload, api_settings):
        super().__init__()
        self.payload = payload
        self.api_settings = api_settings
        
    def run(self):
        try:
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            if self.api_settings['headers']:
                try:
                    custom_headers = json.loads(self.api_settings['headers'])
                    headers.update(custom_headers)
                except json.JSONDecodeError:
                    self.response_received.emit(False, "Invalid headers JSON format", 0)
                    return
            
            # Prepare authentication
            auth = None
            if self.api_settings['auth_type'] == 'basic':
                auth = (self.api_settings['username'], self.api_settings['password'])
            elif self.api_settings['auth_type'] == 'api_key':
                headers['Authorization'] = f"Bearer {self.api_settings['api_key']}"
            
            # Make API request
            response = requests.request(
                method=self.api_settings['method'],
                url=self.api_settings['endpoint'],
                json=self.payload,
                headers=headers,
                auth=auth,
                timeout=self.api_settings['timeout']
            )
            
            if response.status_code in [200, 201, 202, 204]:
                self.response_received.emit(True, f"Success: {response.status_code}", response.status_code)
            else:
                self.response_received.emit(False, f"HTTP {response.status_code}: {response.text[:100]}", response.status_code)
                
        except requests.exceptions.Timeout:
            self.response_received.emit(False, "Request timeout", 0)
        except requests.exceptions.ConnectionError:
            self.response_received.emit(False, "Connection error", 0)
        except requests.exceptions.RequestException as e:
            self.response_received.emit(False, f"Request error: {str(e)}", 0)
        except Exception as e:
            self.response_received.emit(False, f"Unexpected error: {str(e)}", 0)

# ==============================
# MODBUS CONNECTION MANAGER (unchanged)
# ==============================
class ModbusConnectionManager:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.settings = {
            'host': '192.168.51.201',
            'port': 502,
            'timeout': 3,
            'register_start': 0,
            'num_channels': 8,
            'poll_interval': 5000,
            'device_id': 'radix-umx201'
        }
        
    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        # If connected, need to reconnect with new settings
        if self.is_connected:
            self.disconnect()
            
    def connect(self):
        """Establish connection to Modbus device."""
        if self.is_connected:
            return True
            
        try:
            self.client = ModbusTcpClient(
                host=self.settings['host'], 
                port=self.settings['port'], 
                timeout=self.settings['timeout']
            )
            
            if self.client.connect():
                self.is_connected = True
                return True
            else:
                self.client = None
                return False
                
        except Exception as e:
            self.client = None
            self.is_connected = False
            raise ConnectionError(f"Failed to connect: {e}")
    
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
    
    def read_registers(self):
        """Read holding registers from connected device."""
        if not self.is_connected or not self.client:
            raise ConnectionError("Not connected to Modbus device")
            
        try:
            rr = self.client.read_holding_registers(
                address=self.settings['register_start'],
                count=self.settings['num_channels']
            )
            
            if rr.isError():
                raise ModbusException(f"Modbus read error: {rr}")
                
            return rr.registers
            
        except Exception as e:
            # Connection might be lost, mark as disconnected
            self.is_connected = False
            raise

# ==============================
# FTP SETTINGS DIALOG
# ==============================
class FtpSettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("FTP Connection Settings")
        self.setModal(True)
        self.setFixedSize(350, 200)
        
        default_settings = {
            'host': '192.168.51.201',
            'username': 'admin',
            'password': '111',
            'timeout': 10,
            'ws_fetch_enabled': False,  # Add new setting
            #'ws_fetch_url': 'ws://localhost:8000/ws/gateway'  # Add new setting
            'server_url': 'wss://iradixb.bitmutex.com/ws/gateway'
        }
        if settings:
            default_settings.update(settings)
            
        layout = QFormLayout()
        
        # Host
        self.host_edit = QLineEdit(default_settings['host'])
        layout.addRow("FTP Host:", self.host_edit)
        
        # Username
        self.username_edit = QLineEdit(default_settings['username'])
        layout.addRow("Username:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit(default_settings['password'])
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_edit)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(default_settings['timeout'])
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Timeout:", self.timeout_spin)
        
        # Add WebSocket Fetch settings
        self.ws_fetch_checkbox = QCheckBox("Enable WebSocket Fetch Listener")
        self.ws_fetch_checkbox.setChecked(default_settings['ws_fetch_enabled'])
        layout.addRow(self.ws_fetch_checkbox)
        
        self.ws_url_edit = QLineEdit(default_settings['ws_fetch_url'])
        layout.addRow("WebSocket URL:", self.ws_url_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
    def get_settings(self):
        return {
            'host': self.host_edit.text().strip(),
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text(),
            'timeout': self.timeout_spin.value(),
            'ws_fetch_enabled': self.ws_fetch_checkbox.isChecked(),
            'ws_fetch_url': self.ws_url_edit.text().strip()
        }

# Add new WebSocket listener thread class after other thread classes
class FtpWebSocketListenerThread(QThread):
    fetch_requested = pyqtSignal()
    polling_interval_changed = pyqtSignal(int)  # Add new signal
    error = pyqtSignal(str)
    
    def __init__(self, ws_url):
        super().__init__()
        self.ws_url = ws_url
        self.running = True

    async def listen(self):
        while self.running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            if isinstance(data, dict):
                                msg_type = data.get("type")
                                
                                if msg_type == "set_polling_interval":
                                    new_interval = data.get("interval_ms")
                                    if new_interval and new_interval >= 200:
                                        self.polling_interval_changed.emit(new_interval)
                                        
                        except json.JSONDecodeError:
                            if message == "ftp-fetch":
                                self.fetch_requested.emit()
                                
            except Exception as e:
                self.error.emit(str(e))
                await asyncio.sleep(5)

    def run(self):
        asyncio.run(self.listen())

    def stop(self):
        self.running = False

# Update ModbusGui class
class ModbusGui(QWidget):
    def __init__(self):
        super().__init__()
        self.connection_manager = ModbusConnectionManager()
        self.channel_names = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
        self.api_settings = {
            'enabled': False,
             # 'base_url': 'http://localhost:8000',  # Changed to base URL
            'base_url': 'https://iradixb.bitmutex.com',
            
            'method': 'POST',
            'timeout': 10,
            'headers': '{"Content-Type": "application/json"}',
            'auth_type': 'none',
            'api_key': '',
            'username': '',
            'password': ''
        }
        self.ws_settings = {
            'enabled': False,
            #'server_url': 'ws://localhost:8000/ws/gateway'
            'server_url': 'wss://iradixb.bitmutex.com/ws/gateway'
        }
        self.ftp_settings = {
            'host': '192.168.51.201',
            'username': 'admin',
            'password': '111',
            'timeout': 10,
            'ws_fetch_enabled': True,
            #'ws_fetch_url': 'ws://localhost:8000/ws/gateway'
            'ws_fetch_url': 'wss://iradixb.bitmutex.com/ws/gateway'
        }
        self.ftp_ws_thread = None
        # Initialize new components
        self.excel_logger = ExcelLogger()
        self.api_thread = None
        self.ws_thread = None
        self.api_success_count = 0
        self.api_error_count = 0
        self.log_success_count = 0
        self.log_error_count = 0
        self.ws_success_count = 0
        self.ws_error_count = 0
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        self.setWindowTitle("Radix UMX201 Modbus TCP Gateway")
        self.setGeometry(100, 100, 1200, 900)

         # Create Menu Bar
        menubar = QMenuBar(self)
        file_menu = menubar.addMenu("File")
        help_menu = menubar.addMenu("Help")

        # File -> Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help -> About
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Create main splitter for resizable layout
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel for controls and data
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Connection Control Group
        conn_group = QGroupBox("Connection Control")
        conn_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #ffcdd2; color: #d32f2f;")
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.settings_btn = QPushButton("Modbus Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.api_settings_btn = QPushButton("API Settings")
        self.api_settings_btn.clicked.connect(self.open_api_settings)
        
        self.logging_settings_btn = QPushButton("Excel Logging")
        self.logging_settings_btn.clicked.connect(self.open_logging_settings)

        self.ws_settings_btn = QPushButton("WebSocket Settings")
        self.ws_settings_btn.clicked.connect(self.open_ws_settings)
        
        # Add FTP controls
        self.ftp_settings_btn = QPushButton("FTP Settings")
        self.ftp_settings_btn.clicked.connect(self.open_ftp_settings)
        self.ftp_fetch_btn = QPushButton("Fetch FTP Files")
        self.ftp_fetch_btn.clicked.connect(self.fetch_and_send_ftp_files)
        
        conn_layout.addWidget(self.status_label)
        conn_layout.addStretch()
        conn_layout.addWidget(self.ftp_settings_btn)
        conn_layout.addWidget(self.ftp_fetch_btn)
        conn_layout.addWidget(self.logging_settings_btn)
        conn_layout.addWidget(self.api_settings_btn)
        conn_layout.addWidget(self.ws_settings_btn)
        conn_layout.addWidget(self.settings_btn)
        conn_layout.addWidget(self.connect_btn)
        conn_group.setLayout(conn_layout)
        
        # Auto-polling Control Group
        poll_group = QGroupBox("Auto-Polling Control")
        poll_layout = QHBoxLayout()
        
        self.auto_poll_checkbox = QCheckBox("Enable Auto-Polling")
        self.auto_poll_checkbox.setChecked(True)
        self.auto_poll_checkbox.stateChanged.connect(self.toggle_auto_polling)
        
        self.poll_info_label = QLabel(f"Interval: {self.connection_manager.settings['poll_interval']/1000}s")
        
        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.clicked.connect(self.manual_refresh)
        self.refresh_btn.setEnabled(False)
        
        poll_layout.addWidget(self.auto_poll_checkbox)
        poll_layout.addWidget(self.poll_info_label)
        poll_layout.addStretch()
        poll_layout.addWidget(self.refresh_btn)
        poll_group.setLayout(poll_layout)
        
        # Status Groups in Tabs
        status_tabs = QTabWidget()
        
        # API Status Tab
        api_widget = QWidget()
        api_layout = QVBoxLayout()
        
        self.api_status_label = QLabel("API: Disabled")
        self.api_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0;")
        
        api_stats_layout = QHBoxLayout()
        self.api_success_label = QLabel("Success: 0")
        self.api_error_label = QLabel("Errors: 0")
        self.api_last_response_label = QLabel("Last Response: None")
        
        api_stats_layout.addWidget(self.api_success_label)
        api_stats_layout.addWidget(self.api_error_label)
        api_stats_layout.addStretch()
        
        api_layout.addWidget(self.api_status_label)
        api_layout.addLayout(api_stats_layout)
        api_layout.addWidget(self.api_last_response_label)
        api_widget.setLayout(api_layout)
        
        # Excel Logging Status Tab
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        
        self.log_status_label = QLabel("Excel Logging: Disabled")
        self.log_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0;")
        
        log_stats_layout = QHBoxLayout()
        self.log_success_label = QLabel("Logged: 0")
        self.log_error_label = QLabel("Errors: 0")
        self.log_file_label = QLabel("File: None")
        
        log_stats_layout.addWidget(self.log_success_label)
        log_stats_layout.addWidget(self.log_error_label)
        log_stats_layout.addStretch()
        
        log_layout.addWidget(self.log_status_label)
        log_layout.addLayout(log_stats_layout)
        log_layout.addWidget(self.log_file_label)
        log_widget.setLayout(log_layout)

        # WebSocket Status Tab
        ws_widget = QWidget()
        ws_layout = QVBoxLayout()
        
        self.ws_status_label = QLabel("WebSocket: Disabled")
        self.ws_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0;")
        
        ws_stats_layout = QHBoxLayout()
        self.ws_success_label = QLabel("Success: 0")
        self.ws_error_label = QLabel("Errors: 0")
        self.ws_last_msg_label = QLabel("Last Message: None")
        
        ws_stats_layout.addWidget(self.ws_success_label)
        ws_stats_layout.addWidget(self.ws_error_label)
        ws_stats_layout.addStretch()
        
        ws_layout.addWidget(self.ws_status_label)
        ws_layout.addLayout(ws_stats_layout)
        ws_layout.addWidget(self.ws_last_msg_label)
        ws_widget.setLayout(ws_layout)
        
        # Add tabs to status widget
        status_tabs.addTab(api_widget, "API Status")
        status_tabs.addTab(log_widget, "Excel Logging")
        status_tabs.addTab(ws_widget, "WebSocket Status")
        
        # Data Display Groups
        # Raw Registers Group
        raw_group = QGroupBox("Raw Holding Registers")
        raw_layout = QVBoxLayout()
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFixedHeight(60)
        self.raw_text.setFont(QFont("Courier", 9))
        raw_layout.addWidget(self.raw_text)
        raw_group.setLayout(raw_layout)
        
        # Formatted Temperatures Group
        temp_group = QGroupBox("Formatted Temperatures")
        temp_layout = QVBoxLayout()
        self.formatted_text = QTextEdit()
        self.formatted_text.setReadOnly(True)
        self.formatted_text.setFixedHeight(120)
        temp_layout.addWidget(self.formatted_text)
        temp_group.setLayout(temp_layout)
        
        # Channel Names Group
        channels_group = QGroupBox("Channel Names")
        channels_layout = QVBoxLayout()
        self.channels_text = QTextEdit()
        self.channels_text.setReadOnly(True)
        self.channels_text.setFixedHeight(40)
        self.channels_text.setPlainText(", ".join(self.channel_names))
        channels_layout.addWidget(self.channels_text)
        channels_group.setLayout(channels_layout)
        
        # JSON Payload Group
        json_group = QGroupBox("JSON Payload")
        json_layout = QVBoxLayout()
        self.json_text = QTextEdit()
        self.json_text.setReadOnly(True)
        self.json_text.setFont(QFont("Courier", 9))
        json_layout.addWidget(self.json_text)
        json_group.setLayout(json_layout)
        
        # Add all groups to left layout
        left_layout.addWidget(conn_group)
        left_layout.addWidget(poll_group)
        left_layout.addWidget(status_tabs)
        left_layout.addWidget(raw_group)
        left_layout.addWidget(temp_group)
        left_layout.addWidget(channels_group)
        left_layout.addWidget(json_group)
        
        left_widget.setLayout(left_layout)
        
        # Right panel for graphs
        self.graph_widget = TemperatureGraphWidget()
        
        # Add panels to splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(self.graph_widget)
        
        # Set splitter proportions (left panel smaller)
        main_splitter.setSizes([400, 800])
        
        # Main layout
        main_layout = QVBoxLayout()  # Changed to QVBoxLayout to accommodate the menu bar
        main_layout.setMenuBar(menubar)  # Add the menu bar to the layout
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def show_about(self):
        """Displays the custom, polished 'About' dialog."""
        # 'self' (the main window instance) is passed as the parent
        dialog = AboutDialog(self)
        dialog.exec_() # Use exec_() in PyQt5 for modal dialogs

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
    def open_settings(self):
        dialog = ConnectionSettingsDialog(self, self.connection_manager.settings)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            self.connection_manager.update_settings(new_settings)
            
            # Update channel names if number changed
            num_channels = new_settings['num_channels']
            self.channel_names = [f"T{i+1}" for i in range(num_channels)]
            self.channels_text.setPlainText(", ".join(self.channel_names))
            
            # Update graph widget with new channel names
            self.graph_widget.update_channel_names(self.channel_names)
            
            # Update poll interval display
            self.poll_info_label.setText(f"Interval: {new_settings['poll_interval']/1000}s")
            
            # Restart timer if auto-polling is enabled
            if self.auto_poll_checkbox.isChecked() and self.connection_manager.is_connected:
                self.timer.start(new_settings['poll_interval'])
    
    def open_api_settings(self):
        dialog = ApiSettingsDialog(self, self.api_settings)
        if dialog.exec_() == QDialog.Accepted:
            self.api_settings = dialog.get_settings()
            self.update_api_status_display()
            
    def open_logging_settings(self):
        dialog = LoggingSettingsDialog(self, self.excel_logger.settings)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            self.excel_logger.update_settings(new_settings)
            self.update_logging_status_display()

    def open_ws_settings(self):
        dialog = WebSocketSettingsDialog(self, self.ws_settings)
        if dialog.exec_() == QDialog.Accepted:
            self.ws_settings = dialog.get_settings()
            self.update_ws_status_display()
                
    def open_ftp_settings(self):
        dialog = FtpSettingsDialog(self, self.ftp_settings)
        if dialog.exec_() == QDialog.Accepted:
            old_settings = self.ftp_settings.copy()
            self.ftp_settings = dialog.get_settings()
            
            # Handle WebSocket listener changes
            if self.ftp_settings['ws_fetch_enabled']:
                if not self.ftp_ws_thread or old_settings['ws_fetch_url'] != self.ftp_settings['ws_fetch_url']:
                    self.start_ftp_ws_listener()
            else:
                self.stop_ftp_ws_listener()

    def start_ftp_ws_listener(self):
        self.stop_ftp_ws_listener()
        self.ftp_ws_thread = FtpWebSocketListenerThread(self.ftp_settings['ws_fetch_url'])
        self.ftp_ws_thread.fetch_requested.connect(self.fetch_and_send_ftp_files)
        self.ftp_ws_thread.polling_interval_changed.connect(self.update_polling_interval_from_ws)
        self.ftp_ws_thread.error.connect(lambda msg: print(f"FTP WebSocket Error: {msg}"))
        self.ftp_ws_thread.start()

    @pyqtSlot(int)
    def update_polling_interval_from_ws(self, new_interval):
        """Update polling interval when received from WebSocket"""
        self.connection_manager.settings['poll_interval'] = new_interval
        self.poll_info_label.setText(f"Interval: {new_interval/1000}s")
        
        # Restart timer if auto-polling is active
        if self.auto_poll_checkbox.isChecked() and self.connection_manager.is_connected:
            self.timer.stop()
            self.timer.start(new_interval)
        
        # Show notification

        # Show auto-closing message box for 2 seconds
        msg_box = AutoCloseMessageBox(self, timeout=2)
        msg_box.setText(f"Polling interval updated to {new_interval}ms from server")
        msg_box.show()

    def stop_ftp_ws_listener(self):
        if self.ftp_ws_thread and self.ftp_ws_thread.isRunning():
            self.ftp_ws_thread.stop()
            self.ftp_ws_thread.wait()
            self.ftp_ws_thread = None

    def toggle_connection(self):
        if self.connection_manager.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()
            
    def connect_device(self):
        try:
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText("Connecting...")
            
            if self.connection_manager.connect():
                self.status_label.setText(f"Status: Connected to {self.connection_manager.settings['host']}:{self.connection_manager.settings['port']}")
                self.status_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #ccff90; color: #2e7d32;")
                self.connect_btn.setText("Disconnect")
                self.refresh_btn.setEnabled(True)
                
                # Start auto-polling if enabled
                if self.auto_poll_checkbox.isChecked():
                    self.timer.start(self.connection_manager.settings['poll_interval'])
                    
                # Initial data read
                self.update_data()
                
            else:
                raise ConnectionError("Connection failed - device not responding")
                
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to connect to Modbus device:\n{str(e)}")
            self.status_label.setText("Status: Connection Failed")
            self.status_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #ffcdd2; color: #d32f2f;")
            
        finally:
            self.connect_btn.setEnabled(True)
            if not self.connection_manager.is_connected:
                self.connect_btn.setText("Connect")
                
    def disconnect_device(self):
        self.timer.stop()
        self.connection_manager.disconnect()
        
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #ffcdd2; color: #d32f2f;")
        self.connect_btn.setText("Connect")
        self.refresh_btn.setEnabled(False)
        
        # Clear displays
        self.raw_text.clear()
        self.formatted_text.clear()
        self.json_text.clear()
        
    def toggle_auto_polling(self, state):
        if state == 2 and self.connection_manager.is_connected:  # Checked
            self.timer.start(self.connection_manager.settings['poll_interval'])
        else:
            self.timer.stop()
            
    def manual_refresh(self):
        self.update_data()
    
    def update_api_status_display(self):
        if self.api_settings['enabled']:
            base_url = self.api_settings['base_url']
            if len(base_url) > 40:
                base_url = base_url[:37] + "..."
            self.api_status_label.setText(f"API: Enabled - {base_url}")
            self.api_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #c8e6c9; color: #2e7d32;")
        else:
            self.api_status_label.setText("API: Disabled")
            self.api_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0;")
    
    def update_logging_status_display(self):
        if self.excel_logger.settings['enabled']:
            file_name = os.path.basename(self.excel_logger.settings['file_path'])
            if len(file_name) > 30:
                file_name = file_name[:27] + "..."
            self.log_status_label.setText(f"Excel Logging: Enabled")
            self.log_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #c8e6c9; color: #2e7d32;")
            self.log_file_label.setText(f"File: {file_name}")
        else:
            self.log_status_label.setText("Excel Logging: Disabled")
            self.log_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0;")
            self.log_file_label.setText("File: None")

    def update_ws_status_display(self):
        if self.ws_settings['enabled']:
            server_url = self.ws_settings['server_url']
            if len(server_url) > 40:
                server_url = server_url[:37] + "..."
            self.ws_status_label.setText(f"WebSocket: Enabled - {server_url}")
            self.ws_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #c8e6c9; color: #2e7d32;")
        else:
            self.ws_status_label.setText("WebSocket: Disabled")
            self.ws_status_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0;")
    
    
    @pyqtSlot(bool, str, int)
    def on_api_response(self, success, message, status_code):
        if success:
            self.api_success_count += 1
            self.api_last_response_label.setText(f"Last Response: {message} at {time.strftime('%H:%M:%S')}")
            self.api_last_response_label.setStyleSheet("color: green;")
        else:
            self.api_error_count += 1
            self.api_last_response_label.setText(f"Last Error: {message} at {time.strftime('%H:%M:%S')}")
            self.api_last_response_label.setStyleSheet("color: red;")
        
        self.api_success_label.setText(f"Success: {self.api_success_count}")
        self.api_error_label.setText(f"Errors: {self.api_error_count}")
    
    def send_to_api(self, payload):
        if not self.api_settings['enabled']:
            return
            
        # Don't start new request if one is already running
        if self.api_thread and self.api_thread.isRunning():
            return

        # Create a copy of API settings with the full endpoint URL
        api_settings = dict(self.api_settings)
        api_settings['endpoint'] = f"{self.api_settings['base_url']}/data"
            
        self.api_thread = ApiSenderThread(payload, api_settings)
        self.api_thread.response_received.connect(self.on_api_response)
        self.api_thread.start()

    def send_to_websocket(self, payload):
        if not self.ws_settings['enabled']:
            return
        if self.ws_thread and self.ws_thread.isRunning():
            return
        self.ws_thread = WebSocketSenderThread(payload, self.ws_settings)
        self.ws_thread.success.connect(self.on_ws_success)
        self.ws_thread.error.connect(self.on_ws_error)
        self.ws_thread.start()    
        
    @pyqtSlot()
    def on_ws_success(self):
        self.ws_success_count += 1
        self.ws_success_label.setText(f"Success: {self.ws_success_count}")
        self.ws_last_msg_label.setText(f"Last Success: {time.strftime('%H:%M:%S')}")
        self.ws_last_msg_label.setStyleSheet("color: green;")

    @pyqtSlot(str)
    def on_ws_error(self, error_msg):
        self.ws_error_count += 1
        self.ws_error_label.setText(f"Errors: {self.ws_error_count}")
        self.ws_last_msg_label.setText(f"Last Error: {error_msg} at {time.strftime('%H:%M:%S')}")
        self.ws_last_msg_label.setStyleSheet("color: red;")
        
    def log_to_excel(self, payload, temperatures):
        """Log data to Excel file."""
        try:
            if self.excel_logger.log_data(payload, temperatures):
                self.log_success_count += 1
            else:
                if self.excel_logger.settings['enabled']:
                    self.log_error_count += 1
                    
        except Exception as e:
            if self.excel_logger.settings['enabled']:
                self.log_error_count += 1
                print(f"Excel logging failed: {e}")
        
        # Update logging status display
        if self.excel_logger.settings['enabled']:
            self.log_success_label.setText(f"Logged: {self.log_success_count}")
            self.log_error_label.setText(f"Errors: {self.log_error_count}")
        
    def update_data(self):
        if not self.connection_manager.is_connected:
            return
            
        try:
            self.refresh_btn.setEnabled(False)
            
            registers = self.connection_manager.read_registers()
            payload, formatted_temps = self.prepare_payload(registers)
            
            # Update displays
            self.raw_text.setPlainText(str(registers))
            
            # Display formatted temperatures
            temp_lines = [f"{name}: {temp:.1f}°C" for name, temp in zip(self.channel_names, formatted_temps)]
            self.formatted_text.setPlainText("\n".join(temp_lines))
            
            # Update JSON with pretty printing
            self.json_text.setPlainText(json.dumps(payload, indent=2))
            
            # Update graph
            self.graph_widget.add_data_point(formatted_temps)
            
            # Send to API if enabled
            self.send_to_api(payload)

            # Send to WebSocket if enabled
            self.send_to_websocket(payload)
            
            # Log to Excel if enabled
            self.log_to_excel(payload, formatted_temps)
            
            # Update status with last update time
            current_status = self.status_label.text().split(" | ")[0]  # Keep connection info
            self.status_label.setText(f"{current_status} | Last Update: {time.strftime('%H:%M:%S')}")
            
        except (ConnectionError, ModbusException) as e:
            error_message = f"[ERROR] {e}"
            self.raw_text.setPlainText(error_message)
            self.formatted_text.setPlainText(error_message)
            self.json_text.setPlainText(error_message)
            
            # If connection error, disconnect
            if isinstance(e, ConnectionError):
                self.disconnect_device()
                QMessageBox.warning(self, "Connection Lost", "Connection to Modbus device lost. Please reconnect.")
                
        except Exception as e:
            error_message = f"[UNEXPECTED ERROR] {e}"
            self.raw_text.setPlainText(error_message)
            self.formatted_text.setPlainText(error_message)
            self.json_text.setPlainText(error_message)
            
        finally:
            self.refresh_btn.setEnabled(True)
            
    def prepare_payload(self, registers):
        """Format raw register data into meaningful values and JSON structure."""
        # Assuming temperature * 10 (e.g., 255 = 25.5°C)
        formatted_temps = [val / 10.0 for val in registers]
        
        payload = {
            "timestamp": time.time(),
            "device_id": self.connection_manager.settings['device_id'],
            "channels": self.channel_names,
            "temperatures": formatted_temps,
            "raw_registers": registers
        }
        
        return payload, formatted_temps
        
    def closeEvent(self, event):
        """Clean up on application exit."""
        self.timer.stop()
        self.connection_manager.disconnect()
        
        # Wait for API thread to finish
        if self.api_thread and self.api_thread.isRunning():
            self.api_thread.quit()
            self.api_thread.wait(3000)  # Wait up to 3 seconds

        # Wait for WebSocket thread to finish
        if self.ws_thread and self.ws_thread.isRunning():
            self.ws_thread.quit()
            self.ws_thread.wait(3000)  # Wait up to 3 seconds

        # Wait for FTP WebSocket listener thread to finish
        if self.ftp_ws_thread and self.ftp_ws_thread.isRunning():
            self.ftp_ws_thread.stop()
            self.ftp_ws_thread.wait(3000)  # Wait up to 3 seconds
            
        event.accept()

    def fetch_and_send_ftp_files(self):
        """Fetch files from device FTP server, zip them, and send to API."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                ftp = FTP(
                    self.ftp_settings['host'],
                    timeout=self.ftp_settings['timeout']
                )
                ftp.login(
                    self.ftp_settings['username'],
                    self.ftp_settings['password']
                )
                
                files = ftp.nlst()
                local_files = []
                
                # Download files
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
                
                # Send to API with FTP-specific endpoint
                with open(zip_path, 'rb') as zf:
                    files = {'file': ('device_files.zip', zf, 'application/zip')}
                    headers = {'Authorization': f"Bearer {self.api_settings.get('api_key','')}"} if self.api_settings.get('auth_type') == 'api_key' else {}
                    
                    # Use FTP-specific endpoint
                    ftp_endpoint = f"{self.api_settings['base_url']}/data-ftp"
                    
                    response = requests.post(
                        ftp_endpoint,
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                    
                if response.status_code in [200, 201, 202, 204]:
                    save_msg = AutoCloseMessageBox(self)
                    save_msg.setIcon(QMessageBox.Information)
                    save_msg.setWindowTitle("Success")
                    save_msg.setText("Files fetched and sent successfully.")
                    save_msg.setInformativeText(f"API Response: {response.text}")
                    save_btn = save_msg.addButton("Save Locally", QMessageBox.ActionRole)
                    save_msg.addButton(QMessageBox.Ok)
                    save_msg.exec_()

                    if save_msg.clickedButton() == save_btn:
                        save_path, _ = QFileDialog.getSaveFileName(
                            self,
                            "Save Zip File",
                            os.path.join(os.path.expanduser("~"), "device_files.zip"),
                            "Zip Files (*.zip)"
                        )
                        if save_path:
                            import shutil
                            shutil.copy2(zip_path, save_path)
                            success_msg = AutoCloseMessageBox(self)
                            success_msg.setIcon(QMessageBox.Information)
                            success_msg.setWindowTitle("Save Success")
                            success_msg.setText(f"Files saved to: {save_path}")
                            success_msg.exec_()
                else:
                    error_msg = AutoCloseMessageBox(self)
                    error_msg.setIcon(QMessageBox.Warning)
                    error_msg.setWindowTitle("API Error")
                    error_msg.setText(f"API responded with status {response.status_code}")
                    error_msg.setInformativeText(f"Error: {response.text}\n\nWould you like to save the files locally?")
                    save_btn = error_msg.addButton("Save Locally", QMessageBox.ActionRole)
                    error_msg.addButton(QMessageBox.Close)
                    error_msg.exec_()

                    if error_msg.clickedButton() == save_btn:
                        save_path, _ = QFileDialog.getSaveFileName(
                            self,
                            "Save Zip File",
                            os.path.join(os.path.expanduser("~"), "device_files.zip"),
                            "Zip Files (*.zip)"
                        )
                        if save_path:
                            import shutil
                            shutil.copy2(zip_path, save_path)
                            QMessageBox.information(
                                self,
                                "Save Success",
                                f"Files saved to: {save_path}"
                            )
        except Exception as e:
            error_msg = AutoCloseMessageBox(self)
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("FTP Error")
            error_msg.setText(f"Error during FTP operation: {str(e)}")
            if 'zip_path' in locals():  # If zip was created before error
                error_msg.setInformativeText("Would you like to save the downloaded files locally?")
                save_btn = error_msg.addButton("Save Locally", QMessageBox.ActionRole)
            error_msg.addButton(QMessageBox.Close)
            error_msg.exec_()

            if 'zip_path' in locals() and error_msg.clickedButton() == save_btn:
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Zip File",
                    os.path.join(os.path.expanduser("~"), "device_files.zip"),
                    "Zip Files (*.zip)"
                )
                if save_path:
                    import shutil
                    shutil.copy2(zip_path, save_path)
                    QMessageBox.information(
                        self,
                        "Save Success",
                        f"Files saved to: {save_path}"
                    )

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./assets/logo.png"))  # Set application icon (appears in taskbar, alt-tab)
    gui = ModbusGui()
    gui.show()
    sys.exit(app.exec_())