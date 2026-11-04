import itertools

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton
)

from shellarc_msk.mskfs.metafiles_io import MSKFS_MetafilesIo

class DataWrangler(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.make_ui()

    def make_ui(self):
        main_layout = QVBoxLayout(self)

        self.table = QTableWidget(2, 0, self)
            
        main_layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        self.btn_add_col = QPushButton("Add Column", self)
        self.btn_remove_col = QPushButton("Delete Column", self)
        self.btn_add_col.clicked.connect(self.add_column)
        self.btn_remove_col.clicked.connect(self.remove_column)
        button_layout.addWidget(self.btn_add_col)
        button_layout.addWidget(self.btn_remove_col)
        main_layout.addLayout(button_layout)
        self.adjust_to_table_size()

    def adjust_to_table_size(self):
        self.table.viewport().update()

        h = self.table.horizontalHeader().height() + 4
        for i in range(self.table.rowCount()):
            h += self.table.rowHeight(i)
        total_height = h + 85 

        self.resize(self.width(), total_height)

    def redraw_table(self, 
                     data: list[dict[str, str]]
                     ) -> None:
        self.table.setColumnCount(0)
        self.table.setColumnCount(len(data))
        self.table.setHorizontalHeaderLabels([f"Property {col+1}" for col in range(self.table.columnCount())])
        for col in range(len(data)):
            self.table.setItem(0, col, QTableWidgetItem(data[col]["property"]))
            self.table.setItem(1, col, QTableWidgetItem(data[col]["type"]))
        self.table.setVerticalHeaderLabels(["Property", "Type"])
        self.adjust_to_table_size()

    def add_column(self):
        current_col_count = self.table.columnCount()
        new_col_count = current_col_count + 1
        self.table.setColumnCount(new_col_count)
        self.table.setHorizontalHeaderItem(current_col_count, QTableWidgetItem(f"Property {new_col_count}"))
        self.table.setVerticalHeaderLabels(["Property", "Type"])

    def remove_column(self):
        current_col_count = self.table.columnCount()
        if current_col_count <= 0:
            return 

        selected_items = self.table.selectedItems()
        if selected_items:
            target_column = selected_items[0].column()
            self.table.removeColumn(target_column)
        else:
            self.table.removeColumn(current_col_count - 1)
        self.table.setHorizontalHeaderLabels([f"Property {col+1}" for col in range(self.table.columnCount())])

    def make_field_data(self):
        rtn = []
        for col in range(self.table.columnCount()):
            rtn.append({
                "property" : self.table.item(0, col).text(),
                "type" : self.table.item(1, col).text()
            })
        print(f"makefielddata : {rtn}")
        return rtn


class TaskOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        widget_lo = QVBoxLayout(self)

        self.metafiles_io = MSKFS_MetafilesIo()
        field_wrangle_label = QLabel("Field Wrangle")
        widget_lo.addWidget(field_wrangle_label)
        self.field_select_combo = QComboBox()
        self.field_select_combo.clear()
        self.field_select_combo.setEditable(True)
        self.field_select_combo.addItems([k for k in self.metafiles_io.get_all_fields()])
        self.field_select_combo.currentIndexChanged.connect(self.redraw_table)
        widget_lo.addWidget(self.field_select_combo)
        self.field_wrangle_table = DataWrangler()
        self.redraw_table()
        widget_lo.addWidget(self.field_wrangle_table)
        set_field_btn = QPushButton("Set Field")
        set_field_btn.clicked.connect(self.set_field)
        widget_lo.addWidget(set_field_btn)

        self.setLayout(widget_lo)

    def redraw_table(self):
        new_field_name = self.field_select_combo.currentText()
        new_data = self.metafiles_io.get_field(field_name=new_field_name)
        self.field_wrangle_table.redraw_table(
            data=new_data if new_data is not None else []
        )

    def set_field(self):
        self.metafiles_io.set_field(
            field_name=self.field_select_combo.currentText(),
            new_field_def=self.field_wrangle_table.make_field_data()
        )
