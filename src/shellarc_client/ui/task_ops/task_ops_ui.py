import itertools

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton
)

class TaskOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget_lo = QVBoxLayout(self)

        self.setLayout(widget_lo)


