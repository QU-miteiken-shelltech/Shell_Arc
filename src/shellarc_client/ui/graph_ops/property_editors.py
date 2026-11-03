from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton
)

class NodePropertyEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        dialog_lo = QVBoxLayout()
        btn = QPushButton("Test")
        dialog_lo.addWidget(btn)
        self.setLayout(dialog_lo)