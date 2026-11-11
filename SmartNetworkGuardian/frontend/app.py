import sys
import ipaddress
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QMessageBox, QInputDialog)
from backend.database.db import initialize_database
from backend.scanner.network_scanner import discover_local_devices, validate_private_network
from backend.scanner.device_detector import ingest_scan_results
from backend.database.device_model import list_devices
from backend.router.router_manager import active_ipv4_interfaces, detect_default_gateway
from frontend.pages.dashboard import DashboardPage
from frontend.pages.devices import DevicesPage
from frontend.pages.blocked_sites import BlockedSitesPage
from frontend.pages.reports import ReportsPage
from frontend.pages.settings import SettingsPage
from frontend.widgets.status_card import StatusCard

STYLE = """
QMainWindow, QWidget { background:#101722; color:#e8eef7; font-family:'Segoe UI'; font-size:10pt; }
QPushButton { background:#26374d; color:#f4f7fb; border:0; border-radius:7px; padding:9px 14px; }
QPushButton:hover { background:#365273; }
QPushButton:disabled { background:#202a37; color:#8793a2; }
QLabel#pageTitle { font-size:20pt; font-weight:600; }
QFrame#statusCard { background:#1a2635; border:1px solid #2b3b50; border-radius:10px; padding:8px; }
QLabel#cardValue { font-size:20pt; font-weight:600; color:#65d6ad; }
QTableWidget { background:#172231; alternate-background-color:#1d2b3c; gridline-color:#2b3b50; }
QHeaderView::section { background:#26374d; padding:7px; border:0; }
QLineEdit { background:#172231; border:1px solid #35465d; border-radius:6px; padding:8px; color:#fff; }
"""

class ScanWorker(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)
    def __init__(self, cidr):
        super().__init__()
        self.cidr = cidr
    def run(self):
        try:
            self.completed.emit(discover_local_devices(self.cidr))
        except Exception as exc:
            self.failed.emit(str(exc))

class GuardianWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Network Guardian")
        self.resize(1180, 760)
        self.worker = None
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("SMART NETWORK GUARDIAN")
        title.setObjectName("pageTitle")
        self.scan_button = QPushButton("Scan local network")
        self.scan_button.clicked.connect(self.start_scan)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.scan_button)
        outer.addLayout(header)
        cards = QHBoxLayout()
        self.total_card = StatusCard("Known devices", "0")
        self.gateway_card = StatusCard("Default gateway", detect_default_gateway() or "Unavailable")
        self.scope_card = StatusCard("Interfaces", str(len(active_ipv4_interfaces())))
        for card in (self.total_card, self.gateway_card, self.scope_card):
            cards.addWidget(card)
        outer.addLayout(cards)
        body = QHBoxLayout()
        nav = QVBoxLayout()
        self.stack = QStackedWidget()
        self.pages = [DashboardPage(), DevicesPage(), BlockedSitesPage(), ReportsPage(), SettingsPage()]
        for index, (label, page) in enumerate(zip(
            ["Dashboard","Devices","Website blocklist","Reports","Settings"], self.pages)):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, i=index: self.stack.setCurrentIndex(i))
            nav.addWidget(button)
            self.stack.addWidget(page)
        nav.addStretch()
        body.addLayout(nav, 1)
        body.addWidget(self.stack, 5)
        outer.addLayout(body)
        self.statusBar().showMessage("Ready. Scans are manual and restricted to a selected private IPv4 subnet.")
        self.refresh_devices()

    def refresh_devices(self):
        devices = list_devices()
        self.total_card.set_value(len(devices))
        self.pages[1].set_devices(devices)
        self.pages[0].summary.setText(
            f"Inventory contains {len(devices)} observed devices. Missing scan responses do not prove a device is offline.")

    def start_scan(self):
        if self.worker and self.worker.isRunning():
            return
        interfaces = active_ipv4_interfaces()
        options = [f"{x['interface']} — {x['ip']} / {x['netmask']}" for x in interfaces if x.get("netmask")]
        if not options:
            QMessageBox.warning(self, "No network", "No active IPv4 interface with a subnet mask was detected.")
            return
        choice, ok = QInputDialog.getItem(self, "Choose scan interface", "Select the private network:", options, 0, False)
        if not ok:
            return
        selected = interfaces[options.index(choice)]
        cidr = str(ipaddress.IPv4Network(f"{selected['ip']}/{selected['netmask']}", strict=False))
        try:
            validate_private_network(cidr)
        except Exception as exc:
            QMessageBox.warning(self, "Network scope rejected", str(exc))
            return
        confirm = QMessageBox.question(self, "Confirm local scan",
            f"Scan {cidr} using ARP discovery? Only this selected private subnet will be probed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.scan_button.setEnabled(False)
        self.statusBar().showMessage(f"Scanning {cidr}…")
        self.worker = ScanWorker(cidr)
        self.worker.completed.connect(self.scan_complete)
        self.worker.failed.connect(self.scan_failed)
        self.worker.finished.connect(lambda: self.scan_button.setEnabled(True))
        self.worker.start()

    def scan_complete(self, results):
        ingest_scan_results(results)
        self.refresh_devices()
        self.statusBar().showMessage(f"Scan complete: {len(results)} responding devices discovered.")
        QMessageBox.information(self, "Scan complete", f"Discovered {len(results)} responding device(s).")

    def scan_failed(self, message):
        self.statusBar().showMessage("Scan failed.")
        QMessageBox.warning(self, "Scan failed", message)

def launch():
    from backend.config.settings import ensure_directories
    ensure_directories()
    initialize_database()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = GuardianWindow()
    window.show()
    return app.exec()
