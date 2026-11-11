from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from backend.router.router_manager import detect_default_gateway, active_ipv4_interfaces

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Network interfaces"))
        for item in active_ipv4_interfaces():
            layout.addWidget(QLabel(f"{item['interface']}: {item['ip']} / {item['netmask']}"))
        gateway = detect_default_gateway()
        layout.addWidget(QLabel(f"Default gateway: {gateway or 'Not detected'}"))
        layout.addWidget(QLabel("Router filtering: unsupported until a verified router adapter is configured."))
        layout.addStretch()
