from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MetricsPanel(QWidget):
    """Honest empty state until historical measurements are collected."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Historical charts will populate as measurements are collected."))
