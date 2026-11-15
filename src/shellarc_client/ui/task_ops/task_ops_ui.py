import itertools

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton
)

from shellarc_client.ui.task_ops.task_display_chip import TaskDisplayChip

class TaskOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget_lo = QVBoxLayout(self)

        # widget_lo.addWidget(TaskDisplayChip())

        self.setLayout(widget_lo)


