import itertools
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton, QDialog
)

from shellarc_client.ui.task_ops.task_display_chip import TaskDisplayItem
from shellarc_client.ui.task_ops.task_register import RegisterTaskDialog
from shellarc_client.engine.mount import file_manager


class TaskOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget_lo = QVBoxLayout(self)

        scan_lo = QHBoxLayout()
        scan_btn = QPushButton("Scan")
        scan_btn.setFixedWidth(60)
        scan_btn.clicked.connect(self.scan_mount_dir)
        scan_lo.addStretch()
        scan_lo.addWidget(scan_btn)
        widget_lo.addLayout(scan_lo)

        # widget_lo.addWidget(TaskDisplayItem())

        self.setLayout(widget_lo)

    def scan_mount_dir(self):
        mount_dir_info = file_manager.scan_mounted_dir()
        RegisterTaskDialog(mount_info=mount_dir_info, parent=self).exec()


