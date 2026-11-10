from typing import Optional, TYPE_CHECKING
from collections.abc import Iterable

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidgetItem, QDialog, QLineEdit,
    QPushButton, QMessageBox, QGridLayout
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskcm.command_executor import exec_mskcm
if TYPE_CHECKING:
    from shellarc_client.ui.table_ops.table_ops_ui import MSK_TableView

class TableCell(QTableWidgetItem):
    def __init__(self, 
                 field_name: Optional[str]=None,
                 metanode: Optional[MSKDN_Metanode]=None,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = field_name
        self.metanode = metanode if metanode is not None else MSKDN_Metanode(iterable=[])

    def set_diaplay(self, text: str):
        self.setText(text)
        


class CellEditDialog(QDialog):
    def __init__(self, 
                 cell: TableCell,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        dialog_lo = QVBoxLayout()

        field_name_lo = QHBoxLayout()
        field_name_lo.addWidget(QLabel("Field name : "))
        self.field_name_input = QLineEdit(cell.field_name)
        field_name_lo.addWidget(self.field_name_input)
        dialog_lo.addLayout(field_name_lo)

        container_index_lo = QHBoxLayout()
        container_index_lo.addWidget(QLabel("Container index : "))
        self.container_index_input = QLineEdit(cell.container_index)
        container_index_lo.addWidget(self.container_index_input)
        dialog_lo.addLayout(container_index_lo)

        property_lo = QHBoxLayout()
        property_lo.addWidget(QLabel("Property : "))
        self.property_input = QLineEdit(cell.property)
        property_lo.addWidget(self.property_input)
        dialog_lo.addLayout(property_lo)

        dialog_lo.addWidget(QLabel(f"Adress : {cell.adress}"))
        dialog_lo.addWidget(QLabel(f"Value : {cell.value}"))

        btns_lo = QHBoxLayout()
        set_btn = QPushButton("Set")
        set_btn.clicked.connect(self.set_cell)
        btns_lo.addWidget(set_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_cell)
        btns_lo.addWidget(cancel_btn)
        dialog_lo.addLayout(btns_lo)

        self.setLayout(dialog_lo)

    def set_cell(self):
        field_name = self.field_name_input.text()
        
        print("")

    def cancel_cell(self):
        self.reject()

class HeaderEditDialog(QDialog):
    def __init__(self, 
                 logical_index: int,
                 is_vertical: bool,
                 table,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = self.parentWidget().parentWidget().field_name
        
        self.table = table
        self.logical_index = logical_index
        self.is_vertical = is_vertical
        dialog_lo = QVBoxLayout()

        iterator_lo = QGridLayout()
        iterator_label = QLabel("Iterator : ")
        iterator_lo.addWidget(iterator_label, 0, 0)
        self.iterator_input = QLineEdit("")
        iterator_lo.addWidget(self.iterator_input, 0, 1)
        start_pos_label = QLabel("Start at : ")
        iterator_lo.addWidget(start_pos_label, 1, 0)
        self.start_pos_input = QLineEdit("1") #1-start
        self.start_pos_input.setValidator(QIntValidator(bottom=1))
        iterator_lo.addWidget(self.start_pos_input, 1, 1)
        dialog_lo.addLayout(iterator_lo)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_iterator)
        dialog_lo.addWidget(apply_btn)

        self.setLayout(dialog_lo)

    def apply_iterator(self):
        header_pos = self.logical_index
        start_pos = int(self.start_pos_input.text()) - 1 if self.start_pos_input.text() else 0
        try:
            iterator = eval(self.iterator_input.text())
            if not isinstance(iterator, Iterable):
                raise
        except Exception as e:
            QMessageBox.warning(self, "Warning", "Invalid iterator")
            print(e)
            return
        print(iterator)
        print(":::")

        if self.is_vertical:
            current_col_num = self.table.columnCount()
            if current_col_num < start_pos + len(iterator):
                self.table.setColumnCount(start_pos + len(iterator))
                for col in range(start_pos, start_pos + len(iterator)):
                    cell = TableCell()
                    cell.set_diaplay(str(iterator[col - start_pos]))
                    self.table.setItem(header_pos, col, cell)
        else:
            current_row_num = self.table.rowCount()
            if current_row_num < start_pos + len(iterator):
                self.table.setColumnCount(start_pos + len(iterator))
                for row in range(start_pos, start_pos + len(iterator)):
                    cell = TableCell()
                    cell.set_diaplay(str(iterator[row - start_pos]))
                    self.table.setItem(row, header_pos, cell)
        self.accept()


