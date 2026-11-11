from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Network overview")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.summary = QLabel("Run a local scan to populate your device inventory.")
        layout.addWidget(self.summary)
        layout.addStretch()
