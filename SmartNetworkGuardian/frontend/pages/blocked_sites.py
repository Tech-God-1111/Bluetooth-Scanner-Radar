from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
from backend.services.website_service import add_domain, delete_domain
from backend.database.blocked_sites_model import list_sites

class BlockedSitesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.domain = QLineEdit()
        self.domain.setPlaceholderText("example.com")
        add = QPushButton("Add domain")
        remove = QPushButton("Remove selected")
        bar.addWidget(self.domain)
        bar.addWidget(add)
        bar.addWidget(remove)
        layout.addLayout(bar)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Domain","Category"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        add.clicked.connect(self.add_current)
        remove.clicked.connect(self.remove_selected)
        self.refresh()

    def refresh(self):
        rows = list_sites()
        self.table.setRowCount(len(rows))
        for r, item in enumerate(rows):
            self.table.setItem(r,0,QTableWidgetItem(item["domain"]))
            self.table.setItem(r,1,QTableWidgetItem(item["category"]))

    def add_current(self):
        try:
            add_domain(self.domain.text())
            self.domain.clear()
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Invalid domain", str(exc))

    def remove_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            delete_domain(self.table.item(row,0).text())
            self.refresh()
