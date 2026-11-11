from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

class StatusCard(QFrame):
    def __init__(self, title, value="—", parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(title))
        self.value = QLabel(str(value))
        self.value.setObjectName("cardValue")
        layout.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(str(value))
