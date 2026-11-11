from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from backend.services.report_service import export_devices_csv, export_events_pdf

class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Export reports from live database records."))
        csv_button = QPushButton("Export device inventory (CSV)")
        pdf_button = QPushButton("Export recent network events (PDF)")
        layout.addWidget(csv_button)
        layout.addWidget(pdf_button)
        layout.addStretch()
        csv_button.clicked.connect(lambda: self.export(export_devices_csv))
        pdf_button.clicked.connect(lambda: self.export(export_events_pdf))

    def export(self, function):
        try:
            path = function()
            QMessageBox.information(self, "Report created", f"Saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
