from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox
)

from shellarc_msk.mskfs.metafiles_io import MSKFS_MetafilesIo

class DataWrangler(QTableWidget):
    def __init__(self, rows=2, columns=3, parent=None):
        super().__init__(rows, columns, parent)
        # 初期ヘッダーの設定
        self._update_headers()

    def add_column(self):
        current_cols = self.columnCount()
        self.setColumnCount(current_cols + 1)
        self._update_headers()

    def remove_column(self):
        current_cols = self.columnCount()
        if current_cols > 0:
            self.setColumnCount(current_cols - 1)

    def _update_headers(self):
        labels = [f"列 {i+1}" for i in range(self.columnCount())]
        self.setHorizontalHeaderLabels(labels)

class TaskOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget_lo = QVBoxLayout(self)

        self.metafiles_io = MSKFS_MetafilesIo()
        field_wrangle_label = QLabel("Field Wrangle")
        widget_lo.addWidget(field_wrangle_label)
        self.field_select_combo = QComboBox()
        self.field_select_combo.clear()
        self.field_select_combo.addItems([k for k in self.metafiles_io.get_all_fields()])
        self.field_select_combo.currentIndexChanged.connect()
        self.field_wrangle_table = QTableWidget()
        self.fie

        self.setLayout(widget_lo)