from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, 
    QMessageBox
)


from shellarc_client.ui.table_ops.table_cells import TableCell
from shellarc_client.ui.table_ops.table_view import MSK_TableView
from shellarc_client.ui.table_ops.build_table_from_file import TableBuilder
from shellarc_engine.config.read_config import ReadClientConfig
from shellarc_engine.tables import table_capture
from shellarc_msk.mskob.field_obj import MSK_Field


class TableOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lo = QVBoxLayout(self)
        field_lo = QHBoxLayout()
        field_lo.addWidget(QLabel("Field : "))
        self.field_combo = QComboBox()
        self.field_combo.clear()
        self.field_combo.addItems(MSK_Field.field_names())
        self.field_combo.currentIndexChanged.connect(self.switch_field)
        self.field_combo.setFixedWidth(150)
        field_lo.addWidget(self.field_combo)
        field_lo.addStretch()
        self.lo.addLayout(field_lo)

        build_table_lo = QHBoxLayout()
        build_table_label = QLabel("Table : ")
        build_table_label.setMaximumWidth(90)
        build_table_lo.addWidget(build_table_label)
        self.build_table_combo = QComboBox()
        self.build_table_combo.setEditable(True)
        if self.build_table_combo.lineEdit():
            self.build_table_combo.lineEdit().setPlaceholderText("Input or Select")
        self.build_table_combo.clear()
        self.build_table_combo.addItems(
            ReadClientConfig.get_config_item("tables")
        )
        build_table_lo.addWidget(self.build_table_combo)
        build_table_btn = QPushButton("Build table from file")
        build_table_btn.clicked.connect(self.build_table_from_file)
        build_table_lo.addWidget(build_table_btn)
        capture_table_btn = QPushButton("Capture table to disk")
        capture_table_btn.clicked.connect(self.capture_table_to_disk)
        build_table_lo.addWidget(capture_table_btn)
        build_table_lo.addStretch()
        self.lo.addLayout(build_table_lo)

        self.msk_table_view = MSK_TableView()
        self.lo.addWidget(self.msk_table_view)

        btn_lo = QHBoxLayout()
        fit_vert_btn = QPushButton("Fit Vertical")
        fit_vert_btn.clicked.connect(self.fit_table_vert)
        btn_lo.addWidget(fit_vert_btn)
        fit_hor_btn = QPushButton("Fit Horizantal")
        fit_hor_btn.clicked.connect(self.fit_table_hor)
        btn_lo.addWidget(fit_hor_btn)
        fix_width_btn = QPushButton("Fix Width")
        fix_width_btn.clicked.connect(self.fix_cell_width)
        btn_lo.addWidget(fix_width_btn)
        fix_height_btn = QPushButton("Fix Height")
        fix_height_btn.clicked.connect(self.fix_cell_height)
        btn_lo.addWidget(fix_height_btn)
        self.lo.addLayout(btn_lo)

        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_cells)
        self.lo.addWidget(clear_all_btn)

        self.switch_field()

        self.setLayout(self.lo)

    def switch_field(self):
        if hasattr(self, "msk_table_view"):
            do_clear = self.clear_all_cells()
            if not do_clear:
                raise ValueError("Switch rejected")
        new_field_name = self.field_combo.currentText()
        current_field = MSK_Field(field_name=new_field_name)
        self.field_members = [p for p in current_field.field_ls]
        self.field_name = new_field_name

    def build_table_from_file(self):
        table_builder = TableBuilder(
            table_name=self.build_table_combo.currentText(),
            table=self.msk_table_view
        )
        self.field_combo.setCurrentText(table_builder.field_name)
        table_builder.build_table_from_file()

    def capture_table_to_disk(self):
        table_name=self.build_table_combo.currentText()
        if table_name in ReadClientConfig.get_config_item("tables"):
            reply = QMessageBox.question(
                self,
                "Existing",
                f"Are you sure that you want to overwrite table {table_name} ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        table_capture.set_field(field_name=self.field_combo.currentText())
        table_capture.write_to_disk(table_name=table_name)
        self.build_table_combo.clear()
        self.build_table_combo.addItems(
            ReadClientConfig.get_config_item("tables")
        )
        QMessageBox.information(
            self, "Success", "Table file saved."
        )

    def fit_table_vert(self):
        for row in range(self.msk_table_view.rowCount()):
            fitted_row_height = self.msk_table_view.sizeHintForRow(row)
            self.msk_table_view.setRowHeight(row, fitted_row_height)

    def fit_table_hor(self):
        for col in range(self.msk_table_view.columnCount()):
            fitted_col_width = self.msk_table_view.sizeHintForColumn(col)
            self.msk_table_view.setColumnWidth(col, fitted_col_width)

    def fix_cell_width(self):
        standard_width = self.msk_table_view.columnWidth(0)
        for col in range(1, self.msk_table_view.columnCount()):
            self.msk_table_view.setColumnWidth(col, standard_width)

    def fix_cell_height(self):
        standard_height = self.msk_table_view.rowHeight(0)
        for row in range(1, self.msk_table_view.rowCount()):
            self.msk_table_view.setRowHeight(row, standard_height)

    def clear_all_cells(self) -> bool:
        if self.msk_table_view.rowCount() > 1 or self.msk_table_view.columnCount() > 1:
            confirmation = QMessageBox.question(
                self, 
                "Confirmation", 
                "Are you sure that you want to clear this table?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if confirmation == QMessageBox.StandardButton.No:
                return False
        self.msk_table_view.clear()
        self.msk_table_view.setRowCount(1)
        self.msk_table_view.setColumnCount(1)
        self.msk_table_view.setItem(0, 0, TableCell())
        return True

    def change_row_num(self, new_val):
        self.msk_table_view.change_row_num(new_num=new_val)

    def change_col_num(self, new_val):
        self.msk_table_view.change_col_num(new_num=new_val)