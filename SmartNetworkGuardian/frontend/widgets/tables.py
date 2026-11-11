from PyQt6.QtWidgets import QTableWidget

def configure_table(table: QTableWidget):
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
