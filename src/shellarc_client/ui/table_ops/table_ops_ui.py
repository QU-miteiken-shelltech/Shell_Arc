from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton, QAbstractItemView,
    QDialog, QLineEdit
)

from shellarc_msk.mskfs.metafiles_io import MSKFS_MetafilesIo

class TableCell(QTableWidgetItem):
    def __init__(self, 
                 field_name: Optional[str]=None,
                 container_index: Optional[str]=None,
                 property: Optional[str]=None,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = field_name
        self.container_index = container_index
        self.property = property
        self.adress = None
        self.value = None
        self.make_cell_data(
            field_name=field_name,
            container_index=container_index,
            property=property
        )

    def make_cell_data(self,
                       field_name: Optional[str],
                       container_index: Optional[str],
                       property: Optional[str]
                       ) -> None:
        if field_name is None or container_index is None or property is None:
            return
        self.mskfs_metafileio = MSKFS_MetafilesIo()
        self.field_name = field_name
        self.container_index = container_index
        self.property = property
        self.adress = self.mskfs_metafileio.ref_container(
            field_name=field_name,
            container_index=container_index,
            property=property
        )
        self.value = self.mskfs_metafileio.ref_access_map(
            adress=self.adress
        )
        self.setText(self.value)

class RowColCell(TableCell):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    

class CellEditDialig(QDialog):
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
        set

        self.setLayout(dialog_lo)


class MSK_TableView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.itemDoubleClicked.connect(self.item_double_clicked)
        self.setRowCount(4)
        self.setColumnCount(4)
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self.setItem(row, col, TableCell())

    def item_double_clicked(self, clicked_item):
        CellEditDialig(cell=clicked_item).exec()


class TableOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lo = QVBoxLayout(self)
        self.msk_table_view = MSK_TableView()
        self.lo.addWidget(self.msk_table_view)
        self.setLayout(self.lo)