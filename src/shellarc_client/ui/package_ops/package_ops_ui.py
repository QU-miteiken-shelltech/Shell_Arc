from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel
)

class PackageOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lo = QVBoxLayout(self)
        self.lo.addWidget(QLabel("ここはタブ 2 のコンテンツです"))
        self.setLayout(self.lo)

