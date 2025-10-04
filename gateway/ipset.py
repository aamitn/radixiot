import sys
import subprocess
import platform
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QRadioButton, 
                             QLineEdit, QPushButton, QGroupBox, QMessageBox,
                             QButtonGroup, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon


class NetworkConfigThread(QThread):
    """Thread for applying network configuration to avoid GUI freezing"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, adapter, is_dhcp, ip_address, subnet_mask, gateway):
        super().__init__()
        self.adapter = adapter
        self.is_dhcp = is_dhcp
        self.ip_address = ip_address
        self.subnet_mask = subnet_mask
        self.gateway = gateway
        self.os_type = platform.system()
    
    def run(self):
        try:
            if self.os_type == "Windows":
                self._configure_windows()
            elif self.os_type == "Linux":
                self._configure_linux()
            elif self.os_type == "Darwin":  # macOS
                self._configure_macos()
            else:
                self.finished.emit(False, f"Unsupported OS: {self.os_type}")
                return
            
            self.finished.emit(True, "Network configuration applied successfully!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
    
    def _configure_windows(self):
        """Configure network on Windows using netsh"""
        if self.is_dhcp:
            # Set to DHCP
            cmd = f'netsh interface ip set address name="{self.adapter}" source=dhcp'
            subprocess.run(cmd, shell=True, check=True)
            cmd = f'netsh interface ip set dns name="{self.adapter}" source=dhcp'
            subprocess.run(cmd, shell=True, check=True)
        else:
            # Set static IP
            cmd = f'netsh interface ip set address name="{self.adapter}" static {self.ip_address} {self.subnet_mask}'
            if self.gateway:
                cmd += f' {self.gateway}'
            subprocess.run(cmd, shell=True, check=True)
    
    def _configure_linux(self):
        """Configure network on Linux using nmcli or ip commands"""
        if self.is_dhcp:
            # Using NetworkManager (nmcli)
            cmd = f'nmcli con mod "{self.adapter}" ipv4.method auto'
            subprocess.run(cmd, shell=True, check=True)
            cmd = f'nmcli con up "{self.adapter}"'
            subprocess.run(cmd, shell=True, check=True)
        else:
            # Set static IP
            cidr = self._subnet_to_cidr(self.subnet_mask)
            cmd = f'nmcli con mod "{self.adapter}" ipv4.addresses {self.ip_address}/{cidr}'
            subprocess.run(cmd, shell=True, check=True)
            cmd = f'nmcli con mod "{self.adapter}" ipv4.method manual'
            subprocess.run(cmd, shell=True, check=True)
            if self.gateway:
                cmd = f'nmcli con mod "{self.adapter}" ipv4.gateway {self.gateway}'
                subprocess.run(cmd, shell=True, check=True)
            cmd = f'nmcli con up "{self.adapter}"'
            subprocess.run(cmd, shell=True, check=True)
    
    def _configure_macos(self):
        """Configure network on macOS using networksetup"""
        if self.is_dhcp:
            cmd = f'networksetup -setdhcp "{self.adapter}"'
            subprocess.run(cmd, shell=True, check=True)
        else:
            cmd = f'networksetup -setmanual "{self.adapter}" {self.ip_address} {self.subnet_mask}'
            if self.gateway:
                cmd += f' {self.gateway}'
            subprocess.run(cmd, shell=True, check=True)
    
    def _subnet_to_cidr(self, subnet_mask):
        """Convert subnet mask to CIDR notation"""
        return sum([bin(int(x)).count('1') for x in subnet_mask.split('.')])


class EthernetConfigApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.os_type = platform.system()
        self.config_thread = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Ethernet Adapter Configuration Tool")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QLineEdit:disabled {
                background-color: #ecf0f1;
                color: #7f8c8d;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            QRadioButton {
                font-size: 13px;
                spacing: 5px;
            }
            QLabel {
                font-size: 13px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Network Adapter Configuration")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Adapter selection group
        adapter_group = QGroupBox("Select Network Adapter")
        adapter_layout = QVBoxLayout()
        
        adapter_label = QLabel("Available Adapters:")
        self.adapter_combo = QComboBox()
        self.refresh_btn = QPushButton("🔄 Refresh Adapters")
        self.refresh_btn.clicked.connect(self.refresh_adapters)
        
        adapter_layout.addWidget(adapter_label)
        adapter_layout.addWidget(self.adapter_combo)
        adapter_layout.addWidget(self.refresh_btn)
        adapter_group.setLayout(adapter_layout)
        main_layout.addWidget(adapter_group)
        
        # Configuration type group
        config_group = QGroupBox("Configuration Type")
        config_layout = QVBoxLayout()
        
        self.config_button_group = QButtonGroup()
        self.dhcp_radio = QRadioButton("DHCP (Automatic)")
        self.static_radio = QRadioButton("Static IP (Manual)")
        self.dhcp_radio.setChecked(True)
        
        self.config_button_group.addButton(self.dhcp_radio)
        self.config_button_group.addButton(self.static_radio)
        
        self.dhcp_radio.toggled.connect(self.on_config_type_changed)
        
        config_layout.addWidget(self.dhcp_radio)
        config_layout.addWidget(self.static_radio)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Static IP configuration group
        self.static_group = QGroupBox("Static IP Configuration")
        static_layout = QVBoxLayout()
        
        # IP Address
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP Address:")
        ip_label.setMinimumWidth(120)
        self.ip_input = QLineEdit("192.168.51.200")
        self.ip_input.setPlaceholderText("e.g., 192.168.1.100")
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        static_layout.addLayout(ip_layout)
        
        # Subnet Mask
        subnet_layout = QHBoxLayout()
        subnet_label = QLabel("Subnet Mask:")
        subnet_label.setMinimumWidth(120)
        self.subnet_input = QLineEdit("255.255.255.0")
        self.subnet_input.setPlaceholderText("e.g., 255.255.255.0")
        subnet_layout.addWidget(subnet_label)
        subnet_layout.addWidget(self.subnet_input)
        static_layout.addLayout(subnet_layout)
        
        # Gateway (optional)
        gateway_layout = QHBoxLayout()
        gateway_label = QLabel("Gateway (Optional):")
        gateway_label.setMinimumWidth(120)
        self.gateway_input = QLineEdit("")
        self.gateway_input.setPlaceholderText("e.g., 192.168.1.1")
        gateway_layout.addWidget(gateway_label)
        gateway_layout.addWidget(self.gateway_input)
        static_layout.addLayout(gateway_layout)
        
        self.static_group.setLayout(static_layout)
        self.static_group.setEnabled(False)
        main_layout.addWidget(self.static_group)
        
        # Apply button
        self.apply_btn = QPushButton("✓ Apply Configuration")
        self.apply_btn.setMinimumHeight(45)
        self.apply_btn.clicked.connect(self.apply_configuration)
        main_layout.addWidget(self.apply_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #7f8c8d; padding: 10px;")
        main_layout.addWidget(self.status_label)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Load adapters
        self.refresh_adapters()
    
    def on_config_type_changed(self):
        """Enable/disable static IP fields based on configuration type"""
        is_static = self.static_radio.isChecked()
        self.static_group.setEnabled(is_static)
    
    def refresh_adapters(self):
        """Refresh the list of network adapters"""
        self.adapter_combo.clear()
        self.status_label.setText("Refreshing adapters...")
        
        try:
            adapters = self.get_network_adapters()
            if adapters:
                self.adapter_combo.addItems(adapters)
                self.status_label.setText(f"Found {len(adapters)} adapter(s)")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.status_label.setText("No network adapters found")
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        except Exception as e:
            self.status_label.setText(f"Error refreshing adapters: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def get_network_adapters(self):
        """Get list of network adapters based on OS"""
        adapters = []
        
        try:
            if self.os_type == "Windows":
                result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                      capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')[3:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            adapter_name = ' '.join(parts[3:])
                            if 'ethernet' in adapter_name.lower() or 'local' in adapter_name.lower():
                                adapters.append(adapter_name)
            
            elif self.os_type == "Linux":
                result = subprocess.run(['nmcli', '-t', '-f', 'NAME', 'connection', 'show'], 
                                      capture_output=True, text=True, check=True)
                adapters = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            elif self.os_type == "Darwin":  # macOS
                result = subprocess.run(['networksetup', '-listallhardwareports'], 
                                      capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'Hardware Port:' in line and i + 1 < len(lines):
                        port_name = line.split('Hardware Port:')[1].strip()
                        if 'ethernet' in port_name.lower():
                            device_line = lines[i + 1]
                            if 'Device:' in device_line:
                                adapters.append(port_name)
        
        except Exception as e:
            print(f"Error getting adapters: {e}")
        
        return adapters
    
    def validate_ip(self, ip):
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def apply_configuration(self):
        """Apply network configuration"""
        adapter = self.adapter_combo.currentText()
        if not adapter:
            QMessageBox.warning(self, "Warning", "Please select a network adapter")
            return
        
        is_dhcp = self.dhcp_radio.isChecked()
        
        if not is_dhcp:
            # Validate static IP configuration
            ip_address = self.ip_input.text().strip()
            subnet_mask = self.subnet_input.text().strip()
            gateway = self.gateway_input.text().strip()
            
            if not self.validate_ip(ip_address):
                QMessageBox.warning(self, "Invalid IP", "Please enter a valid IP address")
                return
            
            if not self.validate_ip(subnet_mask):
                QMessageBox.warning(self, "Invalid Subnet", "Please enter a valid subnet mask")
                return
            
            if gateway and not self.validate_ip(gateway):
                QMessageBox.warning(self, "Invalid Gateway", "Please enter a valid gateway address")
                return
        else:
            ip_address = subnet_mask = gateway = ""
        
        # Confirm action
        config_type = "DHCP" if is_dhcp else f"Static IP ({ip_address})"
        reply = QMessageBox.question(
            self, 
            "Confirm Configuration",
            f"Apply {config_type} configuration to {adapter}?\n\n"
            "Note: This requires administrator/root privileges.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Disable UI during configuration
        self.apply_btn.setEnabled(False)
        self.status_label.setText("Applying configuration... Please wait.")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        # Start configuration thread
        self.config_thread = NetworkConfigThread(adapter, is_dhcp, ip_address, subnet_mask, gateway)
        self.config_thread.finished.connect(self.on_configuration_finished)
        self.config_thread.start()
    
    def on_configuration_finished(self, success, message):
        """Handle configuration completion"""
        self.apply_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")


def is_admin():
    """Check if the script is running with admin/root privileges"""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return subprocess.run(['id', '-u'], capture_output=True, text=True).stdout.strip() == '0'
    except:
        return False


def run_as_admin():
    """Restart the script with admin privileges"""
    try:
        if platform.system() == "Windows":
            import ctypes
            # Get the command line arguments
            script = sys.argv[0]
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            
            # ShellExecute to run as admin
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script}" {params}', 
                None, 
                1  # SW_SHOWNORMAL
            )
            
            if ret > 32:  # Success
                sys.exit(0)
            else:
                return False
        else:
            # For Linux/macOS, use pkexec or sudo
            if os.path.exists('/usr/bin/pkexec'):
                # Try pkexec first (more user-friendly GUI prompt)
                args = ['pkexec', sys.executable] + sys.argv
            else:
                # Fallback to terminal-based sudo
                terminal_emulators = [
                    ['x-terminal-emulator', '-e'],
                    ['gnome-terminal', '--'],
                    ['konsole', '-e'],
                    ['xterm', '-e'],
                ]
                
                for term in terminal_emulators:
                    if subprocess.run(['which', term[0]], capture_output=True).returncode == 0:
                        args = term + ['sudo', sys.executable] + sys.argv
                        break
                else:
                    # No terminal found, try pkexec without GUI
                    args = ['pkexec', sys.executable] + sys.argv
            
            subprocess.Popen(args)
            sys.exit(0)
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return False
    
    return True


def main():
    # Check if running with admin privileges
    if not is_admin():
        print("Application requires administrator privileges. Requesting elevation...")
        
        # Try to elevate privileges
        if run_as_admin():
            return  # Exit this instance, elevated version will start
        else:
            # If elevation failed, show GUI warning
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Elevation Failed")
            msg.setText("Failed to obtain administrator privileges.")
            msg.setInformativeText(
                "This application requires administrator/root privileges to modify network settings.\n\n"
                "Please manually run the application as administrator:\n"
                "• Windows: Right-click → Run as Administrator\n"
                "• Linux/macOS: Run with sudo or pkexec"
            )
            msg.setDetailedText(
                "Note: Make sure UAC (User Account Control) is not blocking the elevation request on Windows, "
                "or that you have sudo/pkexec available on Linux/macOS."
            )
            msg.exec_()
            sys.exit(1)
    
    # Running with admin privileges - start the application
    app = QApplication(sys.argv)
    window = EthernetConfigApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()