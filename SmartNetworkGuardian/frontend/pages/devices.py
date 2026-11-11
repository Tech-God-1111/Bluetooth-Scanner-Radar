from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

class DevicesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["IP address","MAC address","Hostname","Vendor","Status","Trust"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def set_devices(self, devices):
        self.table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            values = [device.get("ip_address"),device.get("mac_address"),device.get("hostname"),
                      device.get("vendor"),device.get("status"),device.get("trust_status")]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value or "—")))
